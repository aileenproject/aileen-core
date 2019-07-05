from django.conf.urls import url

from data import api

app_name = "data"

urlpatterns = [
    url(
        r"^api/aggregations_by_box_id/(?P<box_id>[^/]+)/",
        api.aggregations_by_box_id,
        name="aggregations_by_box_id",
    ),
    url(r"^api/aggregations/", api.aggregations, name="aggregations"),
    url(
        r"^api/kpis_by_box_id/(?P<box_id>[^/]+)/",
        api.kpis_by_box_id,
        name="kpis_by_box_id",
    ),
]
