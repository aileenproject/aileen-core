from django.conf.urls import url

from box import views, api

app_name = "box"

urlpatterns = [
    url(r"^$", views.dashboard, name="dashboard"),
    url(r"^api/devices/", api.devices, name="devices"),
]
