from datetime import datetime

import pandas as pd

from django.db import models
from django_pandas.managers import DataFrameManager

""" Data models shared between boxes and servers. This is the core data we are collecting."""


class UniqueDevices(models.Model):

    device_id = models.CharField(
        max_length=100, primary_key=True, db_index=True, unique=True
    )
    time_last_seen = models.DateTimeField()

    objects = models.Manager()
    pdobjects = DataFrameManager()

    def __str__(self):
        return str(self.device_id)

    def __repr__(self):
        return "<Device [%s]; last seen: %s>" % (self.device_id, self.time_last_seen)

    @staticmethod
    def find_device_by_id(device_id: str):
        return UniqueDevices.objects.filter(device_id=device_id).first()

    @staticmethod
    def save_from_df(df: pd.DataFrame) -> int:
        """Save devices in the df to the database. Return how many were newly created."""
        created = 0
        for device in df.reset_index(level=0).to_dict("records"):
            device_id = device["device_id"]
            device.pop("device_id")
            unique_device, was_created = UniqueDevices.objects.update_or_create(
                device_id=device_id, defaults=dict(**device)
            )
            if was_created:
                created += 1
                unique_device.time_first_seen = unique_device.time_last_seen
        return created

    @staticmethod
    def to_df():
        return UniqueDevices.pdobjects.all().to_dataframe(index="device_id")


class DevicesEvents(models.Model):

    box_id = models.CharField(max_length=256)
    # refers to BoxSettings or AileenBox, depending on whether we're on a box or on a server
    device = models.ForeignKey(UniqueDevices, null=False, on_delete=models.CASCADE)
    device_power = models.IntegerField()
    time_seen = models.DateTimeField()
    access_point_id = models.CharField(max_length=100)
    total_packets = models.IntegerField()
    packets_captured = models.IntegerField()

    class Meta:
        unique_together = (("device", "time_seen"),)

    objects = models.Manager()
    pdobjects = DataFrameManager()

    def __repr__(self):
        return str(self)

    def __str__(self):
        return "DeviceEvent<%d> device:<%s> time seen: %s" % (
            self.id,
            self.device,
            self.time_seen,
        )

    @staticmethod
    def save_from_df(event_df: pd.DataFrame, box_id: str) -> int:
        """Save device events in the df to the database. Return how many were newly created.
            TODO: move to box app
        """
        created = 0
        if box_id is None or box_id == "":
            raise Exception("No Box ID given.")
        for device_event in event_df.reset_index(level=0).to_dict("records"):
            device_event["box_id"] = box_id

            device: UniqueDevices = UniqueDevices.find_device_by_id(
                device_event["device_id"]
            )

            new_total_packets = int(device_event["total_packets"])
            # use a try except block in case the device does not yet exist
            try:
                last_total_packets = int(
                    DevicesEvents.find_device_by_id(device).iloc[-1].total_packets
                )
                # we need some way to determine the amount of packets that were captured
                # there is a possibility that the airodump-ng csv file had to restart
                # therefor we need to check if this is a continuation of the airodump csv or if it is new
                if last_total_packets < new_total_packets:
                    packets_captured = new_total_packets - last_total_packets
                else:
                    # a device exists but airomon restarted
                    packets_captured = new_total_packets
            except:
                # it is the 1st time a device was seen
                packets_captured = new_total_packets

            device_event.pop("device_id")
            time_seen = device_event["time_seen"]

            device_event.pop("time_seen")
            _, was_created = DevicesEvents.objects.update_or_create(
                device_id=device,
                time_seen=time_seen,
                packets_captured=packets_captured,
                defaults=dict(**device_event),
            )
            if was_created:
                created += 1
        return created

    @staticmethod
    def find_device_by_id(device_id: str):
        return DevicesEvents.pdobjects.filter(device_id=device_id).to_dataframe()

    @staticmethod
    def find_box_by_id(box_id: str):
        return DevicesEvents.pdobjects.filter(box_id=box_id).to_dataframe()


class SeenByHour(models.Model):
    box_id = models.CharField(max_length=256)
    hour_start = models.DateTimeField()
    seen = models.IntegerField()
    seen_also_in_preceding_hour = models.IntegerField()

    objects = models.Manager()
    pdobjects = DataFrameManager()

    class Meta:
        unique_together = (("box_id", "hour_start"),)

    def __str__(self):
        return f"<SeenByHour for {self.hour_start}: {self.seen}, {self.seen_also_in_preceding_hour} on box {self.box_id}>"

    def __repr__(self):
        return str(self)


class SeenByDay(models.Model):
    box_id = models.CharField(max_length=256, unique_for_date="day")
    day_start = models.DateTimeField()
    seen = models.IntegerField()
    seen_also_on_preceding_day = models.IntegerField()
    seen_also_a_week_earlier = models.IntegerField()

    objects = models.Manager()
    pdobjects = DataFrameManager()

    def __str__(self):
        return (
            f"<SeenByDay for {self.day_start}: {self.seen}, {self.seen_also_on_preceding_day},"
            f" {self.seen_also_a_week_earlier} on box {self.box_id}>"
        )

    def __repr__(self):
        return str(self)


class TmuxStatus(models.Model):
    """Status of the Tmux session"""

    box_id = models.CharField(max_length=256)
    airodump_ng = models.BooleanField()
    time_stamp = models.DateTimeField()

    objects = models.Manager()

    def __str__(self):
        return f"Box={self.box_id} time={self.time_stamp} airodump status={self.airodump_ng}"
