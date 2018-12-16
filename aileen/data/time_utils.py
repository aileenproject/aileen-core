from datetime import datetime
import time
import logging

import pytz
from django.conf import settings


logger = logging.getLogger(__name__)


def aileen_now() -> datetime:
    """The current time of the bvp platform. UTC time, localized to the aileen timezone."""
    return as_aileen_time(datetime.utcnow())


def get_timezone():
    """Get a timezone to be used"""
    return pytz.timezone(settings.TIME_ZONE)


def as_aileen_time(dt: datetime) -> datetime:
    """The datetime represented in the timezone of the bvp platform."""
    return naive_utc_from(dt).replace(tzinfo=pytz.utc).astimezone(get_timezone())


def naive_utc_from(dt: datetime) -> datetime:
    """Return a naive datetime, that is localised to UTC if it has a timezone."""
    if not hasattr(dt, "tzinfo") or dt.tzinfo is None:
        # let's hope this is the UTC time you expect
        return dt
    else:
        return dt.astimezone(pytz.utc).replace(tzinfo=None)


def localized_datetime(dt: datetime) -> datetime:
    """Localise a datetime to the timezone of Aileen"""
    return get_timezone().localize(naive_utc_from(dt))


def as_hour(dt: datetime) -> datetime:
    return dt.replace(minute=0, second=0, microsecond=0)


def as_day(dt: datetime) -> datetime:
    return as_hour(dt).replace(hour=0)


def get_most_recent_hour() -> datetime:
    return as_hour(aileen_now())


def sleep_until_interval_is_complete(start_time, interval_in_seconds):
    """ take a break, so in all we will have spent x seconds, incl. runtime"""
    run_time = time.time() - start_time
    rest_interval_in_seconds = interval_in_seconds - (run_time % interval_in_seconds)
    logger.info("Sleeping for %.2f seconds ..." % rest_interval_in_seconds)
    time.sleep(rest_interval_in_seconds)
