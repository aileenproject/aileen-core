from django.conf.urls import url

from box import views

app_name = "box"

urlpatterns = [
    url(r"^$", views.dashboard, name="dashboard"),
]
