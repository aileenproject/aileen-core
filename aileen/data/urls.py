from data import api
from django.conf.urls import url

app_name = "data"

urlpatterns = [
    url(
        r"^api/devices_by_box_id/(?P<box_id>[^/]+)/",
        api.devices_by_box_id,
        name="devices_by_box_id",
    ),
    url(r"^api/devices/", api.devices, name="devices"),
]
