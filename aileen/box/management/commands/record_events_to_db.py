import logging
import time
from datetime import datetime

import numpy as np
import pandas as pd
import pytz
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from box.airo_tasks.watch_airodump_csv import read_airodump_csv_and_return_df
from box.models import BoxSettings
from box.utils.dir_handling import build_tmp_dir_name
from data.models import DevicesEvents, UniqueDevices
from data.time_utils import sleep_until_interval_is_complete

logger = logging.getLogger(__name__)


def update_database_with_new_and_updated_devices(airodump_events_df: pd.DataFrame):
    """
    From  known devices and latest airodump input, we compute what should go to the database:

    We are interested in the most recent events (device presence seen by airodump), which we do not yet know about.
    There is some set computing involved to single these out.

    Based on this information, we also update the unique devices table (this includes adding new ones seen
    for the first time). Every device gets time_last_seen set to what airomon reported just now.
    """
    logger.info(f"Length of airodump_df: {len(airodump_events_df)}")

    # Load a df of unique devices, with a compatible timezone
    known_devices_df = UniqueDevices.to_df()
    if len(known_devices_df.index) > 0:
        known_devices_df.time_last_seen = known_devices_df.time_last_seen.dt.tz_convert(
            settings.TIME_ZONE
        )

    # Create a dataframe of devices which were just discovered for the first time
    new_devices_events_df = airodump_events_df[
        ~airodump_events_df.device_id.isin(known_devices_df.index)
    ]

    # Append the new devices to the known ones, as well
    known_devices_df = known_devices_df.append(
        new_devices_events_df[["device_id", "time_seen"]]
        .rename(columns={"time_seen": "time_last_seen"})
        .set_index("device_id"),
        sort=False,
    )

    # Join the events which airodump just recorded with information about known devices.
    # The joined df has both time_seen (airodump event) and time_last_seen.
    old_dt = datetime(1970, 1, 1, 1, 1, 1, tzinfo=pytz.timezone(settings.TIME_ZONE))
    airodump_plus_device_data_df = (
        airodump_events_df.set_index("device_id")
        .join(known_devices_df)
        .replace(np.NaN, old_dt)
    )

    # Now we can distill what update events actually matter to us (airodump keeps old events in its csv):
    # the ones where last_seen > time_last_seen. This excludes both old entries in the airodump file, where both
    # time_seen and time_last_seen are longer ago and new devices, which have both time_seen and time_last_seen
    # set to just now. Thus, we add the latter here.
    updated_device_events_df = (
        airodump_plus_device_data_df[
            airodump_plus_device_data_df.time_seen
            > airodump_plus_device_data_df.time_last_seen
        ]
        .drop(columns=["time_last_seen"])
        .append(new_devices_events_df.set_index("device_id"))
    )

    # To store updates to the devices table, format the updated device events as unique devices
    unique_devices_with_recent_updates_df = updated_device_events_df[
        ["time_seen"]
    ].rename(columns={"time_seen": "time_last_seen"})

    # And now it is time to let the database know about all of this.
    # First the devices, then events, so that the FK relation from events to devices works.
    with transaction.atomic():
        created = UniqueDevices.save_from_df(unique_devices_with_recent_updates_df)
        logger.info(
            f"Finished saving {len(unique_devices_with_recent_updates_df.index)} unique devices {created} were new."
        )

        box_settings = BoxSettings.objects.first()
        if box_settings is None:
            raise Exception(
                "No box settings yet. Please create some in the admin panel."
            )
        created = DevicesEvents.save_from_df(
            updated_device_events_df, box_settings.box_id
        )
        logger.info(
            f"Finished saving {len(updated_device_events_df.index)} updated device events, {created} were new."
        )


def csv_file_to_db(tmp_path: str, csv_filename_prefix: str):
    logger.info(f"{settings.TERM_LBL} Starting to watch the airodump file ...")
    box_settings = BoxSettings.objects.first()

    while True:
        start_time = time.time()
        airodump_df = read_airodump_csv_and_return_df(
            tmp_path, csv_filename_prefix, box_settings.min_power
        )
        update_database_with_new_and_updated_devices(airodump_df)
        sleep_until_interval_is_complete(
            start_time, settings.AIRODUMP_LOG_INTERVAL_IN_SECONDS
        )

        print()


class Command(BaseCommand):
    help = "The process of writing the airodump data to database"

    def handle(self, *args, **kwargs):
        tmp_dir_name = build_tmp_dir_name()
        csv_file_to_db(tmp_dir_name, settings.AIRODUMP_FILE_PREFIX)
