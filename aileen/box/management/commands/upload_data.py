import logging
import time

from django.core.management.base import BaseCommand
from django.core.serializers import serialize
import pytz

import requests
from django.conf import settings
from box.models import BoxSettings
from data.models import DevicesEvents, UniqueDevices, SeenByDay, SeenByHour, TmuxStatus
from data.time_utils import (
    get_most_recent_hour,
    sleep_until_interval_is_complete,
    as_day,
    get_timezone,
)


logger = logging.getLogger(__name__)


def upload_latest_events():
    """Check box settings, upload events and also affected devices."""
    box_settings = BoxSettings.objects.first()

    # get events which have an ID higher than the last uploaded one
    events_query = DevicesEvents.objects.filter(box_id=box_settings.box_id)
    latest_event = box_settings.events_uploaded_until
    if latest_event is not None:
        events_query = events_query.filter(id__gt=latest_event.id)
    events = events_query.order_by("id").all()[: settings.UPLOAD_MAX_NUMBER_PER_REQUEST]

    # get queries for devices mentioned in these events and record the latest event
    device_queries = {}
    new_latest_event = None  # cannot use events.last() as it doesn't understand slicing
    for event in events:
        device_queries[event.device_id] = UniqueDevices.objects.filter(
            device_id=event.device_id
        )
        new_latest_event = event

    if len(events) > 0:
        logger.info(
            f"I collected {len(events)} events to send, from {events.first().id} to {new_latest_event.id}."
        )
    else:
        logger.info("No events found. Nothing to send.")
        return
    logger.info(f"I collected {len(device_queries.keys())} devices to send.")

    payload = dict(
        devices=f"[{','.join(serialize('json', d)[1:-1] for d in device_queries.values())}]",
        events=serialize("json", events),
    )

    response = requests.post(
        f"{box_settings.server_url}/api/postEvents/{box_settings.box_id}/",
        data=payload,
        headers={"Authorization": box_settings.upload_token},
    )

    if response.status_code == 200:
        logger.info(
            f"Marking {new_latest_event.id} as the last Id successfully uploaded."
        )
        box_settings.events_uploaded_until = new_latest_event
        box_settings.save()
    else:
        logger.error(
            f"Server responded with code {response.status_code} ({response.text})."
        )


def upload_latest_aggregations():
    """Upload latest aggregations."""
    box_settings = BoxSettings.objects.first()
    # build queries
    hour_query = SeenByHour.objects.filter(box_id=box_settings.box_id)
    day_query = SeenByDay.objects.filter(box_id=box_settings.box_id)
    latest_upload_time = box_settings.aggregations_uploaded_until
    if latest_upload_time is not None:
        hour_query = hour_query.filter(hour_start__gt=latest_upload_time)
        day_query = day_query.filter(
            day_start__gte=as_day(latest_upload_time.astimezone(get_timezone()))
        )
    # query
    seen_by_hour = hour_query.order_by("hour_start").all()[
        : settings.UPLOAD_MAX_NUMBER_PER_REQUEST
    ]
    seen_by_day = day_query.order_by("day_start").all()[
        : settings.UPLOAD_MAX_NUMBER_PER_REQUEST
    ]

    if len(seen_by_hour) == 0:
        logger.info("No aggregations found. Nothing to send.")
        return

    # find out until what aggregation time we won't upload again next time - current hour needs to stay out.
    current_hour_start = get_most_recent_hour()
    latest_aggregation_time = None
    for aggregation in [
        sbh for sbh in seen_by_hour if sbh.hour_start < current_hour_start
    ]:
        latest_aggregation_time = aggregation.hour_start

    logger.info(
        f"I collected {len(seen_by_hour)} hour aggregation(s) and {len(seen_by_day)} day aggregation(s) to send,"
        f" starting at {seen_by_hour.first().hour_start}."
    )
    if latest_aggregation_time is not None:
        logger.info(
            f" - next time I will not upload finished times up until {latest_aggregation_time}."
        )

    payload = dict(
        seen_by_hour=serialize("json", seen_by_hour),
        seen_by_day=serialize("json", seen_by_day),
    )

    response = requests.post(
        f"{box_settings.server_url}/api/postAggregations/{box_settings.box_id}/",
        data=payload,
        headers={"Authorization": box_settings.upload_token},
    )

    if response.status_code == 200:
        if latest_aggregation_time is not None:
            logger.info(
                f"Marking {latest_aggregation_time} as the last aggregation time we will not upload next time."
            )
            box_settings.aggregations_uploaded_until = latest_aggregation_time
            box_settings.save()
    else:
        logger.error(
            f"Server responded with code {response.status_code} ({response.text})."
        )


def upload_tmux_status():
    """upload the tmux_status"""
    box_settings = BoxSettings.objects.first()

    tmux_status_query = TmuxStatus.objects.filter(box_id=box_settings.box_id)
    latest_status = box_settings.tmux_status_uploaded_until
    if latest_status is not None:
        tmux_status_query = tmux_status_query.filter(id__gt=latest_status.id)
    statuss = tmux_status_query.order_by("id").all()[
        : settings.UPLOAD_MAX_NUMBER_PER_REQUEST
    ]

    # get queries for tmux status mentioned in these tmux statuss' and record the latest tmux status
    tmux_status_queries = {}
    new_latest_status_query = None
    for status in statuss:
        tmux_status_queries[status.box_id] = TmuxStatus.objects.filter(
            box_id=status.box_id
        )
        new_latest_status_query = status

    if len(statuss) > 0:
        logger.info(
            f"I collected {len(statuss)} tmux status (of {len(tmux_status_queries.keys())} box)"
            f" to send, from {statuss.first().id} to {new_latest_status_query.id}."
        )
    else:
        logger.info("No tmux status found. Nothing to send.")
        return

    payload = dict(tmux_statuss=serialize("json", statuss))

    response = requests.post(
        f"{box_settings.server_url}/api/postTmuxStatus/{box_settings.box_id}/",
        data=payload,
        headers={"Authorization": box_settings.upload_token},
    )

    if response.status_code == 200:
        logger.info(
            f"Marking {new_latest_status_query.id} as the last status Id successfully uploaded."
        )
        box_settings.tmux_status_uploaded_until = new_latest_status_query
        box_settings.save()
    else:
        logger.error(
            f"Server responded with code {response.status_code} ({response.text})."
        )


class Command(BaseCommand):
    help = "The process of uploading data to a Aileen server."

    def handle(self, *args, **kwargs):
        box_settings = BoxSettings.objects.first()
        if box_settings is None:
            logger.error(
                f"{settings.TERM_LBL} No box settings found. Upload attempt aborted ..."
            )
            return
        logger.info(
            f"{settings.TERM_LBL} Starting the uploader against {box_settings.server_url} ..."
        )

        while True:
            start_time = time.time()

            if settings.UPLOAD_EVENTS is True:
                upload_latest_events()
            upload_latest_aggregations()
            upload_tmux_status()
            sleep_until_interval_is_complete(
                start_time, settings.UPLOAD_INTERVAL_IN_SECONDS
            )

            print()
