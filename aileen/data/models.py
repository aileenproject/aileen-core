from datetime import datetime

import pandas as pd
from django.db import models

# we get generic json support from a third-party lib,
# even though native support would be given - for pg only.
from jsonfield import JSONField

from django_pandas.managers import DataFrameManager

""" Data models shared between boxes and servers. This is the core data we are collecting."""


class Observables(models.Model):

    observable_id = models.CharField(
        max_length=100, primary_key=True, db_index=True, unique=True
    )
    time_last_seen = models.DateTimeField()

    objects = models.Manager()
    pdobjects = DataFrameManager()

    def __str__(self):
        return str(self.device_id)

    def __repr__(self):
        return "<Observable [%s]; last seen: %s>" % (
            self.observable_id,
            self.time_last_seen,
        )

    @staticmethod
    def find_observable_by_id(observable_id: str):
        return Observables.objects.filter(observable_id=observable_id).first()

    @staticmethod
    def save_from_df(df: pd.DataFrame) -> int:
        """Save observablees in the df to the database. Return how many were newly created."""
        created = 0
        for observable in df.reset_index(level=0).to_dict("records"):
            observable_id = observable["observable_id"]
            observable.pop("observable_id")
            observable, was_created = Observables.objects.update_or_create(
                observable_id=observable_id, defaults=dict(**observable)
            )
            if was_created:
                created += 1
                observable.time_first_seen = observable.time_last_seen
        return created

    @staticmethod
    def to_df():
        return Observables.pdobjects.all().to_dataframe(index="observables_id")


class Events(models.Model):

    box_id = models.CharField(max_length=256)
    time_seen = models.DateTimeField()
    # refers to BoxSettings or AileenBox, depending on whether we're on a box or on a server
    observable = models.ForeignKey(Observables, null=False, on_delete=models.CASCADE)
    observations = JSONField()

    """
    device_power = models.IntegerField()
    access_point_id = models.CharField(max_length=100)
    total_packets = models.IntegerField()
    packets_captured = models.IntegerField()
    """

    class Meta:
        unique_together = (("observable", "time_seen"),)

    objects = models.Manager()
    pdobjects = DataFrameManager()

    def __repr__(self):
        return str(self)

    def __str__(self):
        return "Event<%d> observable:<%s> time seen: %s" % (
            self.id,
            self.observable,
            self.time_seen,
        )

    @staticmethod
    def save_from_df(event_df: pd.DataFrame, box_id: str) -> int:
        """Save events in the df to the database. Return how many were newly created.
        """
        created = 0
        if box_id is None or box_id == "":
            raise Exception("No Box ID given.")
        for event in event_df.reset_index(level=0).to_dict("records"):
            event["box_id"] = box_id

            observable: Observables = Observables.find_observable_by_id(
                event["observable_id"]
            )

            new_total_packets = int(event["total_packets"])
            # use a try except block in case the device does not yet exist
            try:
                last_total_packets = int(
                    Events.find_device_by_id(device).iloc[-1].total_packets
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

            event.pop("observable_id")
            time_seen = event["time_seen"]

            event.pop("time_seen")
            _, was_created = Observables.objects.update_or_create(
                observable_id=observable,
                time_seen=time_seen,
                packets_captured=packets_captured,
                defaults=dict(**event),
            )
            if was_created:
                created += 1
        return created

    @staticmethod
    def find_by_observable_id(observable_id: str):
        return Events.pdobjects.filter(observable_id=observable_id).to_dataframe()

    @staticmethod
    def find_by_box_id(box_id: str):
        return Events.pdobjects.filter(box_id=box_id).to_dataframe()


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
    sensor_status = models.BooleanField()
    time_stamp = models.DateTimeField()

    objects = models.Manager()

    def __str__(self):
        return f"Box={self.box_id} time={self.time_stamp} sensor status={self.sensor_status}"
