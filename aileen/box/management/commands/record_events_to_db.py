import logging
import time
from datetime import datetime
import importlib

import numpy as np
import pandas as pd
import pytz
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from box.models import BoxSettings
from box.utils.dir_handling import get_sensor, build_tmp_dir_name
from box.utils.privacy_utils import hash_observable_ids
from data.models import Events, Observables
from data.time_utils import sleep_until_interval_is_complete

logger = logging.getLogger(__name__)


def update_database_with_new_and_updated_observables(sensor_events_df: pd.DataFrame):
    """
    From known observables and latest sensor input, we compute what should go to the database:

    We are interested in the most recent events, which we do not yet know about.
    There is some set computing involved to single these out.

    Based on this information, we also update the observables table (this includes adding new ones seen
    for the first time). Every observable gets time_last_seen set to what the sensor reported just now.
    """
    logger.info(f"Length of sensor df: {len(sensor_events_df)}")

    # Load a df of observables, with a compatible timezone
    known_observables_df = Observables.to_df()
    if len(known_observables_df.index) > 0:
        known_observables_df.time_last_seen = known_observables_df.time_last_seen.dt.tz_convert(
            settings.TIME_ZONE
        )

    # Create a dataframe of observables which were just discovered for the first time
    new_observables_events_df = sensor_events_df[
        ~sensor_events_df.observable_id.isin(known_observables_df.index)
    ]

    # Append the new observables to the known ones, as well
    known_observables_df = known_observables_df.append(
        new_observables_events_df[["observable_id", "time_seen"]]
        .rename(columns={"time_seen": "time_last_seen"})
        .set_index("observable_id"),
        sort=False,
    )

    # Join the events which the sensor just recorded with information about known observables.
    # The joined df has both time_seen and time_last_seen.
    old_dt = datetime(1970, 1, 1, 1, 1, 1, tzinfo=pytz.timezone(settings.TIME_ZONE))
    events_plus_observable_data_df = (
        sensor_events_df.set_index("observable_id")
        .join(known_observables_df)
        .replace(np.NaN, old_dt)
    )

    # Now we can distill which updated events actually matter to us
    # (sensors might report already known events to us):
    # the ones where last_seen > time_last_seen. This excludes both old entries in the sensor data, where both
    # time_seen and time_last_seen are longer ago and new observables, which have both time_seen and time_last_seen
    # set to just now. Thus, we add the latter here.
    updated_events_df = (
        events_plus_observable_data_df[
            events_plus_observable_data_df.time_seen
            > events_plus_observable_data_df.time_last_seen
        ]
        .drop(columns=["time_last_seen"])
        .append(new_observables_events_df.set_index("observable_id"))
    )

    # do custom value adjustments if wanted
    sensor = get_sensor()
    if hasattr(sensor, "adjust_event_value"):

        def adjust_event(event_df):
            observable: Observables = Observables.find_observable_by_id(
                event_df.name  # observable_id
            )
            last_event_value = None
            try:
                last_event_df = Events.find_by_observable_id(observable.id).iloc[-1]
                last_event_value = last_event_df["value"]
            except:
                pass
            event_df["value"], event_df["observations"] = sensor.adjust_event_value(
                event_df["value"],
                last_event_value,
                event_df["observations"],
                last_event_df["observations"],
                observable,
            )
            return event_df

        updated_events_df = updated_events_df.apply(adjust_event, axis=1)

    # To store updates to the observables table,
    # format the updated events as observables.
    observables_with_recent_updates_df = updated_events_df[["time_seen"]].rename(
        columns={"time_seen": "time_last_seen"}
    )

    # And now it is time to let the database know about all of this.
    # First the observables, then events, so that the FK relation from events to observables works.
    with transaction.atomic():
        created = Observables.save_from_df(observables_with_recent_updates_df)
        logger.info(
            f"Finished saving {len(observables_with_recent_updates_df.index)} observables, {created} were new."
        )

        box_settings = BoxSettings.objects.first()
        if box_settings is None:
            raise Exception(
                "No box settings yet. Please create some in the admin panel."
            )
        created = Events.save_from_df(updated_events_df, box_settings.box_id)
        logger.info(
            f"Finished saving {len(updated_events_df.index)} updated observable events, {created} were new."
        )


def sensor_data_to_db(tmp_path: str):
    logger.info(f"{settings.TERM_LBL} Starting to transfer the sensor input to db ...")
    sensor = get_sensor()

    while True:
        start_time = time.time()
        sensor_data_df = sensor.get_latest_reading_as_df(tmp_path)

        # check if expected columns are given
        for expected_column in ("observable_id", "time_seen", "value", "observations"):
            if expected_column not in sensor_data_df.columns:
                logger.error(
                    "The sensor module function 'get_latest_reading_as_df' did not return a dataframe"
                    " with the column %s."
                    " Instead, the dataframe only has these columns: %s",
                    expected_column, sensor_data_df.columns
                )

        # hash observable IDs if wanted
        sensor_data_df["observable_id"] = sensor_data_df["observable_id"].map(
            lambda x: hash_observable_ids(str(x))
        )

        update_database_with_new_and_updated_observables(sensor_data_df)
        sleep_until_interval_is_complete(
            start_time, settings.SENSOR_LOG_INTERVAL_IN_SECONDS
        )

        print()


class Command(BaseCommand):
    help = "The process of writing the sensor data to database"

    def handle(self, *args, **kwargs):
        tmp_dir_name = build_tmp_dir_name()
        sensor_data_to_db(tmp_dir_name)
