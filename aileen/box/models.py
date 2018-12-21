import uuid

from django.core.exceptions import ValidationError
from django.db import models


class BoxSettings(models.Model):
    """Settings used by an AileenBox. Usually filled via the admin view during registration/calibration."""

    box_id = models.CharField(max_length=256, default=uuid.uuid4, editable=False)
    server_url = models.URLField()
    upload_token = models.CharField(max_length=120)
    events_uploaded_until = models.ForeignKey(
        "data.DevicesEvents", null=True, blank=True
    )
    aggregations_uploaded_until = models.DateTimeField(null=True)
    tmux_status_uploaded_until = models.ForeignKey(
        "data.TmuxStatus", null=True, blank=True
    )

    objects = models.Manager()

    class Meta:
        verbose_name = "Aileen box settings"
        verbose_name_plural = "Settings for this aileen box"

    def __repr__(self):
        return (
            f"<Box {self.box_id} uploaded to {self.server_url} events until {self.events_uploaded_until}"
            f" and aggregations until {self.aggregations_uploaded_until}>"
        )

    def save(self, **kwargs):
        """Overload save to make sure there will only ever be one row with settings per box."""
        count = BoxSettings.objects.all().count()

        if count == 0 or self.has_save_permission():
            super(BoxSettings, self).save(**kwargs)
        else:
            raise ValidationError(
                "Cannot save a second set of settings, please edit the existing one."
            )

    def has_save_permission(self):
        return BoxSettings.objects.filter(id=self.id).exists()
