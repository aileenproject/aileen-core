from django.db import models
from djgeojson.fields import PointField

import numpy as np

from data.models import SeenByDay
 

class AileenBox(models.Model):

    geom = PointField()
    box_id = models.CharField(max_length=256)
    name = models.CharField(max_length=100)
    description = models.TextField()

    objects = models.Manager()

    class Meta:
        verbose_name = "Aileen box"
        verbose_name_plural = "Aileen boxes"

    @property
    def average_devices_per_day(self):
        devices_each_day = SeenByDay.pdobjects.filter(box_id=self.box_id).to_dataframe()
        devices_each_day = devices_each_day[devices_each_day["seen"] != 0]
        mean = devices_each_day["seen"].mean()
        if mean is np.nan:
            return 0
        return int(devices_each_day["seen"].mean())

    def __str__(self):
        return f"{self.name}: {self.description}, located at {self.geom}"

    def __repr__(self):
        return self.name

    def __unicode__(self):
        return self.title
