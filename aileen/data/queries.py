import logging
from datetime import datetime
from typing import Dict, List

import pandas as pd
from django.conf import settings

from data.models import DevicesEvents, SeenByDay, SeenByHour

"""
TODO: these are not all "queries". Two of these are very special (pandas-related) utility functions.
"""

logger = logging.getLogger(__name__)


def prepare_df_datetime_index(
    df: pd.DataFrame, time_column="time_seen"
) -> pd.DataFrame:
    """
    Utility function which prepares an event dataframe to become time series data
    """
    df.astype(str, inplace=True)  # needed to have the json send easily
    df.rename(columns={time_column: "time"}, inplace=True)
    df.index = df["time"]
    del df["time"]
    if not df.index.empty:
        if df.index.tzinfo is not None:
            df.index = df.index.tz_convert(settings.TIME_ZONE)
        else:
            df.index = df.index.tz_localize(settings.TIME_ZONE)
    for field_name in (
        "id",
        "box_id",
        "total_packets",
    ):  # TODO: not the job of this function
        if field_name in df.columns:
            df.drop(field_name, 1, inplace=True)
    return df


def unique_devices_per_bin_size(df: pd.DataFrame, bin_size: str) -> List:
    """
    Utility function for the Device Events dataframe. This function returns
    a json ready dictionary in the following format
    [{'time_seen': '2018-11-17 21:00:00', 'number_of_devices_seen': 0},{...}]
    """

    unique_clients_per_unit_time_df = (
        df.resample(bin_size)["device"]
        .unique()
        .to_frame()["device"]
        .str.len()  # pythonic way to count a list
        .to_frame()
        .rename(columns={"device": "devices"})
        .reset_index()
    )

    unique_clients_per_unit_time_df["time"] = unique_clients_per_unit_time_df[
        "time"
    ].map(
        lambda x: x.strftime("%s")
    )  # unix time for D3
    data = unique_clients_per_unit_time_df.to_dict("records")

    return data


def number_of_times_client_was_seen_per_bin_size(df: pd.DataFrame, bin_size: str):
    """
    takes in a dataframe containing one device id and returns the following:
    [{'time_seen': '2018-11-16 08:00:00', 'number_of_times_device_was_seen': 2},{...}]
    """

    times_client_was_seen_per_bin_size = (
        df.resample(bin_size)["device_id"]
        .count()
        .to_frame()
        .rename(columns={"device_id": "devices", "time_seen": "time"})
        .reset_index()
    )

    times_client_was_seen_per_bin_size["time"] = times_client_was_seen_per_bin_size[
        "time"
    ].map(lambda x: x.strftime("%s"))
    data = times_client_was_seen_per_bin_size.to_dict("records")

    return data


def get_unique_device_ids_seen(
    box_id: str, start_time: datetime, end_time: datetime
) -> List[str]:
    return [
        row["device_id"]
        for row in DevicesEvents.objects.filter(box_id=box_id)
        .filter(time_seen__gte=start_time)
        .filter(time_seen__lte=end_time)
        .values("device_id")
        .distinct()
        .all()
    ]


def compute_kpis(box_id="None") -> Dict:
    """Compute KPIs for a box, over all available aggregated data.
        * running_since: datetime
        * devices_seen_per_day: float
        * busyness: { by_hour: {hour_of_day: int, num_devices: int, percentage_margin_to_second: float}
                      by_day: {weekday: str, num_devices: int, percentage_margin_to_second: float}
                    }
        * stasis: { by_hour: float (percentage), by_day: float, by_week: float (percentage)}
    """
    # basic structure first
    kpis = dict(running_since=None, devices_seen_per_day=None)
    kpis["busyness"] = dict(
        by_hour=dict(
            hour_of_day=None, num_devices=None, percentage_margin_to_second=None
        ),
        by_day=dict(weekday=None, num_devices=None, percentage_margin_to_second=None),
    )
    kpis["stasis"] = dict(by_hour=None, by_day=None, by_week=None)
    kpis["running_since"] = (
        SeenByHour.objects.filter(box_id=box_id)
        .order_by("hour_start")
        .first()
        .hour_start
    )

    seen_by_hour_df = prepare_df_datetime_index(
        SeenByHour.pdobjects.filter(box_id=box_id).to_dataframe(
            fieldnames=["hour_start", "seen", "seen_also_in_preceding_hour"]
        ),
        time_column="hour_start",
    )

    seen_by_day_df = prepare_df_datetime_index(
        SeenByDay.pdobjects.filter(box_id=box_id).to_dataframe(
            fieldnames=[
                "day_start",
                "seen",
                "seen_also_on_preceding_day",
                "seen_also_a_week_earlier",
            ]
        ),
        time_column="day_start",
    )

    if len(seen_by_hour_df.index) > 0:
        hour_means = seen_by_hour_df.seen.groupby([seen_by_hour_df.index.hour]).mean()
        if len(hour_means.index) > 1:
            hour_means.sort_values(ascending=False, inplace=True)
            kpis["busyness"]["by_hour"]["num_devices_mean"] = round(hour_means.mean(), 2)
            kpis["busyness"]["by_hour"]["hour_of_day"] = hour_means.index[0]
            kpis["busyness"]["by_hour"]["num_devices"] = round(
                hour_means[hour_means.index[0]], 2
            )
            # Compute this with mean as reference - we measure increase from there
            kpis["busyness"]["by_hour"]["percentage_margin_to_mean"] = round(
                (
                    hour_means.loc[hour_means.index[0]]
                    - hour_means.mean()
                )
                / hour_means.mean()
                * 100,
                2,
            )
        kpis["stasis"]["by_hour"] = round(
            seen_by_hour_df.seen_also_in_preceding_hour.mean()
            / seen_by_hour_df.seen.mean()
            * 100,
            2,
        )

    if len(seen_by_day_df.index) > 0:
        # dayofweek are 0 to 6 here
        day_means = seen_by_day_df.seen.groupby([seen_by_day_df.index.dayofweek]).mean()
        if len(day_means.index) > 1:
            kpis["busyness"]["by_day"]["num_devices_mean"] = round(day_means.mean(), 2)
            day_means.sort_values(ascending=False, inplace=True)
            week_day_names = (
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
                "Sunday",
            )
            kpis["busyness"]["by_day"]["weekday"] = week_day_names[day_means.index[0]]
            kpis["busyness"]["by_day"]["num_devices"] = day_means[day_means.index[0]]
            kpis["busyness"]["by_day"]["percentage_margin_to_mean"] = round(
                (day_means.loc[day_means.index[0]] - day_means.mean())
                / day_means.mean()
                * 100,
                2,
            )
        kpis["devices_seen_per_day"] = round(seen_by_day_df.seen.mean(), 2)
        kpis["stasis"]["by_day"] = round(
            seen_by_day_df.seen_also_on_preceding_day.mean()
            / seen_by_day_df.seen.mean()
            * 100,
            2,
        )
        kpis["stasis"]["by_week"] = round(
            seen_by_day_df.seen_also_a_week_earlier.mean()
            / seen_by_day_df.seen.mean()
            * 100,
            2,
        )

    return kpis


# ------------------------------------------------------------------------------
#                        Nasty Eric queries
# ------------------------------------------------------------------------------


def data_from_selected_device(device_id) -> pd.DataFrame:
    device_info = (
        DevicesEvents.find_device_by_id(device_id)
        .drop("device", 1)
        .drop("id", 1)
        .drop("total_packets", 1)
    )
    device_info["time_seen"] = device_info["time_seen"].map(
        lambda x: x.replace(tzinfo=None).strftime("%Y-%m-%d %H:%M:%S")
    )

    return device_info


def data_for_device_per_unit_time(device_id):

    bin_size = "H"

    device_df = prepare_df_datetime_index(DevicesEvents.find_device_by_id(device_id))

    device_id = device_df.device.resample(bin_size).count().to_frame()
    device_power = device_df.device_power.resample(bin_size).mean().to_frame().round()
    device_packets = device_df.packets_captured.resample(bin_size).sum().to_frame()
    # # Join all of the individual dataframes and format

    id_power_packets = (
        device_power.join(device_id)
        .join(device_packets)
        .dropna()
        .abs()
        .rename(columns={"device": "seen_count"})
        .reset_index()
    )
    id_power_packets["time"] = id_power_packets["time"].map(
        lambda x: x.replace(tzinfo=None).timestamp()
    )

    data = id_power_packets.to_dict("records")
    return data
