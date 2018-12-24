from django.conf.urls import url

<<<<<<< HEAD
from calibration import api, views
=======
from calibration import views, api
>>>>>>> merging_with_nic

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
