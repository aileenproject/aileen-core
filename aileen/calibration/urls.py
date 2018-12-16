from django.conf.urls import url

from calibration import views, api

app_name = "calibration"

urlpatterns = [
    url(r"^calibration", views.calibration, name="calibration"),
    url("^api/selected_device", api.selected_device, name="selected_device"),
    url(
        "^api/device_per_unit_time",
        api.device_per_unit_time,
        name="device_per_unit_time",
    ),
]
