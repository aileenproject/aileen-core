from datetime import datetime, timedelta

import pytz
from django.core.management.base import BaseCommand

from data.models import DevicesEvents, UniqueDevices, SeenByDay, SeenByHour
from data.queries import (
    unique_devices_per_bin_size,
    prepare_df_datetime_index,
    get_unique_device_ids_seen,
)
from box.models import BoxSettings
from server.models import AileenBox

# django_pandas
# https://github.com/chrisdev/django-pandas


def query_db():
    # box_id = BoxSettings.objects.first().box_id
    boxes = [
        row["box_id"] for row in SeenByDay.objects.values("box_id").distinct().all()
    ]

    def get_box_mean(box_id: str):
        devices_each_day = SeenByDay.pdobjects.filter(box_id=box_id).to_dataframe()
        devices_each_day = devices_each_day[devices_each_day["seen"] != 0]
        return int(devices_each_day["seen"].mean())

    box_info = dict(box_name=None, mean_devices_each_day=None)

    for box_id in boxes:
        box_info["box_name"] = AileenBox.objects.filter(box_id=box_id).get().name
        box_info["mean_devices_each_day"] = get_box_mean(box_id)
    print(box_info)

    # box_device = DevicesEvents.find_box_by_id(box_id)
    # #    print(box_devices)
    #
    # box_name = AileenBox.objects.filter(box_id=box_id).get().name
    #
    # box_device.astype(str, inplace=True)
    # box_device.rename(columns={"time_seen": "time"}, inplace=True)
    # box_device.index = box_device["time"]
    # del box_device["time"]
    # box_device.drop("id", 1, inplace=True)
    # box_device.drop("box_id", 1, inplace=True)
    # box_device.drop("total_packets", 1, inplace=True)
    #
    # df = unique_devices_per_bin_size(box_device, "H")
    # print(df)

    #     print(Devices_Events.pdobjects.filter(time_seen__year=2018))

    # Nils = "A0:C9:A0:EF:57:DC"

    # df = Unique_Devices.to_df()
    # print(Unique_Devices.find_device_by_id("60:F4:45:97:FC:E5"))
    # print(df)
    # ud = Unique_Devices.to_df()
    # #print(ud)
    # print(ud)
    # print(Devices_Events.find_device_by_id("60:F4:45:97:FC:E5"))
    """
    de = Devices_Events.objects.all()
    start_time = datetime.strptime("2018-11-11 00:00:01", "%Y-%m-%d %H:%M:%S").replace(tzinfo=pytz.timezone("Europe/Amsterdam"))
    print(start_time)
    end_time = datetime.strptime("2018-11-15 00:00:01", "%Y-%m-%d %H:%M:%S").replace(tzinfo=pytz.timezone("Europe/Amsterdam"))
    print(end_time)
    print(Devices_Events.objects.filter(time_seen__range=[start_time, end_time]))
    """
    # start_time = datetime.strptime("2018-11-11 00:00:01", "%Y-%m-%d %H:%M:%S").replace(
    #     tzinfo=pytz.timezone("Europe/Amsterdam")
    # )
    #
    # end_time = datetime.strptime("2018-11-15 00:00:01", "%Y-%m-%d %H:%M:%S").replace(
    #     tzinfo=pytz.timezone("Europe/Amsterdam")
    # )
    #
    # one_week_ago = (datetime.today() - timedelta(days=7)).replace(
    #     tzinfo=pytz.timezone("Europe/Amsterdam")
    # )
    #    df = Devices_Events.find_devices_seen_after_date(one_week_ago)

    #    df = prepare_df_datetime_index(Devices_Events.find_devices_seen_after_date(one_week_ago))
    # print(
    #     unique_clients_per_hour(
    #         prepare_df_datetime_index(
    #             Devices_Events.find_devices_seen_after_date(one_week_ago)
    #         )
    #     )
    # # )
    # Started = DevicesEvents.objects.order_by("time_seen").first()
    # # first_time = Devices_Events.objects.get(pk=Started)
    #
    # Ud = DevicesEvents.find_device_by_id("00:16:0A:28:20:56").reset_index()
    # Ud["time_seen"] = Ud["time_seen"].map(lambda x: x.strftime("%Y-%m-%d %H:%M:%S"))
    # Ud = Ud.to_json(orient="records", date_unit="s", date_format="iso")

    # device_info = DevicesEvents.find_device_by_id(device_id)#.drop('device_id',1)
    # device_info["time_seen"] = device_info["time_seen"].map(
    #     lambda x: x.strftime("%Y-%m-%d %H:%M:%S")
    # )
    # df = device_info.resample("H")["device_id"]
    #
    # print(device_info)
    #

    #
    # data = prepare_df_datetime_index(
    #         DevicesEvents.find_device_by_id(device_id)
    #     )
    # print(data)
    # print(len(data))
    # df = data.resample('H')['device_id'].sum()
    # print(dir(df))
    # print(df)
    #
    # import pandas as pd
    # import sqlite3 as lite
    #
    # con = lite.connect('db.sqlite3')
    # query = "SELECT * FROM detect_devices_devices_events"
    # df = pd.read_sql_query(query, con)
    #
    # df.astype(str, inplace=True)  # needed to have the json send easily
    # df.index = df["time_seen"]
    # del df["time_seen"]
    # df.drop("id", 1, inplace=True)
    #
    # ericdf = df[df['device_id_id'] == device_id]
    #
    # print(len(ericdf))

    # df = DevicesEvents.find_device_by_id(device_id)
    # df = prepare_df_datetime_index(df)
    # df = (
    #     df.resample("H")["device_id"]
    #     .count()
    #     .to_frame()
    #     .reset_index()
    #     .to_json(orient="records", date_unit="s", date_format="iso")
    # )
    #
    # print(len(df))
    # print(df)
    #
    # print(UniqueDevices.str())

    # device_df = prepare_df_datetime_index(
    #     DevicesEvents.find_device_by_id("60:F4:45:97:FC:E5")
    # )
    #
    # device_id = device_df.device_id.resample("H").count().to_frame()
    # device_power = device_df.device_power.resample("H").mean().to_frame().round()
    # device_packets = device_df.packets_captured.resample("H").sum().to_frame()
    #
    # id_power_packets = (
    #     device_power.join(device_id)
    #     .join(device_packets)
    #     .dropna()
    #     .abs()
    #     .rename(columns={"device_id": "number_of_times_device_was_seen"})
    #     .reset_index()
    # )
    # id_power_packets["time_seen"] = id_power_packets["time_seen"].map(
    #     lambda x: x.strftime("%Y-%m-%d %H:%M:%S")
    # )
    # data = id_power_packets.to_dict("records")
    # print(data)
    #
    # total_unique_devices = UniqueDevices.objects.all().count()
    # first_time_a_device_was_seen = (
    #     DevicesEvents.objects.order_by("time_seen")
    #     .first()
    #     .time_seen.strftime("%Y-%m-%d %H:%M:%S")
    # )


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        query_db()
