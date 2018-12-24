<<<<<<< HEAD
import logging
import random
import sys
import uuid
from datetime import datetime, timedelta
from typing import Optional

import iso8601
import pandas as pd
from django.core.management.base import BaseCommand
from django.db import transaction

from data.models import SeenByDay, SeenByHour
from data.time_utils import get_most_recent_hour, get_timezone
from server.models import AileenBox

=======
from typing import Optional
import sys
import logging
from datetime import datetime, timedelta
import uuid
import random

import iso8601
import pandas as pd
from django.db import transaction
from django.core.management.base import BaseCommand

from data.time_utils import get_most_recent_hour, get_timezone
from data.models import SeenByDay, SeenByHour
from server.models import AileenBox


>>>>>>> merging_with_nic
logger = logging.getLogger(__name__)


def makeup_number_devices(dt: datetime, options: dict) -> float:
    weekday_multipliers = [1, 1.1, 1.45, 1.31, 1, 1, 1.13]
    x = options["base_busyness"] * random.gauss(1, 0.05)
    if dt.hour >= 23 or dt.hour <= 8:
        x *= 2 / 3  # night time activity is lower
    if options["peak_time"] == "morning" and 10 <= dt.hour <= 13:
        x *= 1.5  # morning peak
        if dt.hour == 11:  # one hour stands out
            x *= 1.17
    if options["peak_time"] == "afternoon" and 16 <= dt.hour <= 19:
        x *= 1.5  # afternoon peak
        if dt.hour == 17:  # one hour stands out
            x *= 1.15
    x *= weekday_multipliers[dt.weekday()]
    return x


def make_new_aileenbox_or_none(options: dict) -> Optional[AileenBox]:
    """ make a new aileen_box if that is needed """
    aileen_box = None
    if options["box_id"] is None:
        options["box_id"] = uuid.uuid4()
    if AileenBox.objects.filter(box_id=options["box_id"]).first() is None:
        aileen_box = AileenBox(
            geom={
                "type": "Point",
                "coordinates": [float(l) for l in options["location"].split(",")],
            },
            box_id=options["box_id"],
            name="Box made for static data",
            description="...",
        )
    return aileen_box


class Command(BaseCommand):
    help = "Create some static data for testing. Uses some basic assumptions about differences between hours and days."

    def add_arguments(self, parser):
        parser.add_argument(
            "--start",
            nargs="?",
            type=str,
            help="Start of data (full hour). Defaults to a week ago.",
        )
        parser.add_argument(
            "--end",
            nargs="?",
            type=str,
            help="End of data (full hour). Defaults to last hour.",
        )
        parser.add_argument(
            "--box_id",
            nargs="?",
            type=str,
            help="ID of box, If empty, a new box is created.",
        )
        parser.add_argument(
            "--base_busyness",
            nargs="?",
            type=int,
            default=80,
            help="Devices seen during a non-peak hour.",
        )
        parser.add_argument(
            "--peak_time",
            nargs="?",
            type=str,
            default="afternoon",
            help="'morning' or 'afternoon'.",
        )
        parser.add_argument(
            "--location",
            nargs="?",
            type=str,
            default="4.925,52.393",
            help="Latitude and longitude if the bix is created anew, separated by a comma.",
        )

    def handle(self, *args, **options):
        # figure out start and end
        if options["start"] is None:
            options["start"] = get_most_recent_hour() - timedelta(days=7)
        else:
            options["start"] = iso8601.parse_date(options["start"]).astimezone(
                get_timezone()
            )
        if options["end"] is None:
            options["end"] = get_most_recent_hour()
        else:
            options["end"] = iso8601.parse_date(options["end"]).astimezone(
                get_timezone()
            )
        if options["start"] >= options["end"]:
            print("Start cannot be before end.")
            sys.exit(2)

        aileen_box = make_new_aileenbox_or_none(options)

        if "peak_time" not in options or options["peak_time"] not in (
            "morning",
            "afternoon",
        ):
            print("peak_time needs to be either morning or afternoon.")
            sys.exit(2)

        logger.info(
            "create_static_data command was called. Start: %s, End: %s, Box: %s ..."
            % (options["start"], options["end"], options["box_id"])
        )

        hourly = []
        daily = []

        time_slots = pd.date_range(options["start"], options["end"], freq="1H")
        for dt in time_slots:
            x = makeup_number_devices(dt, options)
            hourly.append(
                SeenByHour(
                    box_id=options["box_id"],
                    hour_start=dt,
                    seen=int(x),
                    seen_also_in_preceding_hour=int(x / random.choice([1.5, 2.5, 4])),
                )
            )
            if dt.hour == 0 and len(hourly) >= 24:
                sum_by_hours = sum([sbh.seen for sbh in hourly[-24:]])
                seen_this_day = int(sum_by_hours / 2.0)
                daily.append(
                    SeenByDay(
                        box_id=options["box_id"],
                        day_start=dt - timedelta(hours=24),
                        seen=int(seen_this_day),
                        seen_also_on_preceding_day=int(
                            seen_this_day / random.choice([1.5, 2.5, 4])
                        ),
                        seen_also_a_week_earlier=int(
                            seen_this_day / random.choice([1.5, 2.5, 4])
                        ),
                    )
                )

        # Now save to the database
        with transaction.atomic():
            if aileen_box is not None:
                aileen_box.save()
            for aggregation in hourly + daily:
                print("Saving %s ..." % aggregation)
                aggregation.save()
