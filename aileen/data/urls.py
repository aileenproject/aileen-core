from django.conf.urls import url

from data import api

app_name = "data"

urlpatterns = [
    url(
        r"^api/observables_by_box_id/(?P<box_id>[^/]+)/",
        api.observables_by_box_id,
        name="observables_by_box_id",
    ),
    url(
        r"^api/kpis_by_box_id/(?P<box_id>[^/]+)/",
        api.kpis_by_box_id,
        name="kpis_by_box_id",
    ),
]
