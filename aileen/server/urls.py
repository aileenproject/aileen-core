from djgeojson.views import GeoJSONLayerView
from django.conf.urls import url, include
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy

from server import models, api, views


app_name = "server"

urlpatterns = [
    url(r"^$", views.Landing.as_view(), name="landing"),
    url(
        r"login/$",
        auth_views.LoginView.as_view(template_name="server/login.html"),
        name="login",
    ),
    url(
        r"^logout/$",
        auth_views.LogoutView.as_view(next_page=reverse_lazy("server:landing")),
        name="logout",
    ),
    url(r"^home", views.Home.as_view(), name="home"),
    url(
        r"^data.geojson$",
        GeoJSONLayerView.as_view(
            model=models.AileenBox, properties=("name", "box_id", "geom", "average_devices_per_day")
        ),
        name="aileen_box_location",
    ),
    url(r"^box/(?P<box_id>[^/]+)", views.box, name="box"),
    # ------------------------------------------------------------------------------
    #                                    API
    # ------------------------------------------------------------------------------
    url(
        r"^api/average_number_of_devices_seen_by_box",
        api.average_number_of_devices_seen_by_box,
        name="average_number_of_devices_seen_by_box",
    ),

    url(r"^api/postEvents/(?P<box_id>[^/]+)/", api.post_events, name="postEvents"),
    url(
        r"^api/postAggregations/(?P<box_id>[^/]+)/",
        api.post_aggregations,
        name="postEvents",
    ),
    url(
        r"^api/postTmuxStatus/(?P<box_id>[^/]+)/",
        api.post_tmux_status,
        name="post_tmux_status",
    ),
]
