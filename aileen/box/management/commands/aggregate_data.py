import logging
import time
from datetime import datetime, timedelta
from typing import List

import pandas as pd
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from box.models import BoxSettings
from data.models import SeenByDay, SeenByHour, TmuxStatus
from data.queries import get_unique_device_ids_seen
from data.time_utils import as_day, as_hour, get_most_recent_hour, sleep_until_interval_is_complete

logger = logging.getLogger(__name__)


def aggregate_hour(hour_start: datetime) -> SeenByHour:
    """Aggregate hourly seen events for the hour starting at the passed time."""
    box_settings = BoxSettings.objects.first()

    unique_device_ids_this_hour = get_unique_device_ids_seen(
        box_id=box_settings.box_id,
        start_time=hour_start,
        end_time=hour_start + timedelta(hours=1),
    )
    unique_device_ids_preceding_hour = get_unique_device_ids_seen(
        box_id=box_settings.box_id,
        start_time=hour_start - timedelta(hours=1),
        end_time=hour_start,
    )
    seen_in_both = [
        device_id
        for device_id in unique_device_ids_this_hour
        if device_id in unique_device_ids_preceding_hour
    ]

    aggregation = SeenByHour(box_id=box_settings.box_id, hour_start=hour_start)
    existing_aggregation = (
        SeenByHour.objects.filter(box_id=box_settings.box_id)
        .filter(hour_start=hour_start)
        .first()
    )
    if existing_aggregation:
        aggregation = existing_aggregation

    aggregation.seen = len(unique_device_ids_this_hour)
    aggregation.seen_also_in_preceding_hour = len(seen_in_both)

    return aggregation


def aggregate_day(day_start: datetime) -> SeenByDay:
    """Aggregate daily seen events for the day starting at the passed time."""
    box_settings = BoxSettings.objects.first()
    unique_device_ids_today = get_unique_device_ids_seen(
        box_id=box_settings.box_id,
        start_time=day_start,
        end_time=day_start + timedelta(days=1),
    )
    unique_device_ids_preceding_day = get_unique_device_ids_seen(
        box_id=box_settings.box_id,
        start_time=day_start - timedelta(days=1),
        end_time=day_start,
    )
    seen_both_today_and_yesterday = [
        device_id
        for device_id in unique_device_ids_today
        if device_id in unique_device_ids_preceding_day
    ]

    unique_device_ids_a_week_earlier = get_unique_device_ids_seen(
        box_id=box_settings.box_id,
        start_time=day_start - timedelta(days=7),
        end_time=day_start - timedelta(days=6),
    )
    seen_both_today_and_a_week_earlier = [
        device_id
        for device_id in unique_device_ids_today
        if device_id in unique_device_ids_a_week_earlier
    ]

    aggregation = SeenByDay(box_id=box_settings.box_id, day_start=day_start)
    existing_aggregation = (
        SeenByDay.objects.filter(box_id=box_settings.box_id)
        .filter(day_start=day_start)
        .first()
    )
    if existing_aggregation:
        aggregation = existing_aggregation

    aggregation.seen = len(unique_device_ids_today)
    aggregation.seen_also_on_preceding_day = len(seen_both_today_and_yesterday)
    aggregation.seen_also_a_week_earlier = len(seen_both_today_and_a_week_earlier)

    return aggregation


def get_unaggregated_hours(dt_from: datetime, dt_until: datetime) -> List[datetime]:
    """Look back in time to see which hours (start time) are not yet aggregated, but should be."""
    hours_without_aggregations = []
    box_settings = BoxSettings.objects.first()
    for hour in pd.date_range(as_hour(dt_from), as_hour(dt_until), freq="1H"):
        aggregation = (
            SeenByHour.objects.filter(box_id=box_settings.box_id)
            .filter(hour_start=hour)
            .first()
        )
        if aggregation is None:
            # add this hour to be aggregated - if airodump was on at any time during.
            if (
                TmuxStatus.objects.filter(time_stamp__gte=hour)
                .filter(time_stamp__lt=hour + timedelta(hours=1))
                .filter(airodump_ng=True)
                .count()
                > 0
            ):
                hours_without_aggregations.append(hour)
    return hours_without_aggregations


def get_unaggregated_days(dt_from: datetime, dt_until: datetime) -> List[datetime]:
    """Look back in time to see which days (start time) are not yet aggregated, but should be,"""
    days_without_integration = []
    box_settings = BoxSettings.objects.first()
    for day in pd.date_range(as_day(dt_from), as_day(dt_until), freq="1D"):
        aggregation = (
            SeenByDay.objects.filter(box_id=box_settings.box_id)
            .filter(day_start=day)
            .first()
        )
        if aggregation is None:
            # add this day to be aggregated - if airodump was on at any time during.
            if (
                TmuxStatus.objects.filter(time_stamp__gte=day)
                .filter(time_stamp__lt=day + timedelta(hours=24))
                .filter(airodump_ng=True)
                .count()
                > 0
            ):
                days_without_integration.append(day)
    return days_without_integration


def aggregate_data_to_db():
    logger.info(f"{settings.TERM_LBL} Starting to aggregate event data ...")

    while True:
        start_time = time.time()
        recent_hour = get_most_recent_hour()
        look_back_until = recent_hour - timedelta(
            hours=7 * 24
        )  # catch up until a week of yet unaggregated data

        # This aggregates all unaggregated hours/days up until the preceding one, plus the currently active one.
        with transaction.atomic():
            for hour in get_unaggregated_hours(
                look_back_until, recent_hour - timedelta(hours=1)
            ) + [get_most_recent_hour()]:
                seen_by_hour = aggregate_hour(hour)
                seen_by_hour.save()
                logger.info(f"Saved {seen_by_hour}")

            for day in get_unaggregated_days(
                look_back_until, recent_hour - timedelta(hours=24)
            ) + [get_most_recent_hour().replace(hour=0)]:
                seen_by_day = aggregate_day(day)
                seen_by_day.save()
                logger.info(f"Saved {seen_by_day}")

        sleep_until_interval_is_complete(
            start_time, settings.UPLOAD_INTERVAL_IN_SECONDS
        )

        print()


class Command(BaseCommand):
    help = "The process of aggregating the airodump data in the database"

    def handle(self, *args, **kwargs):
        aggregate_data_to_db()
