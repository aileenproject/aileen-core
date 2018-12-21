from box import views
from django.conf.urls import url

app_name = "box"

urlpatterns = [url(r"^$", views.dashboard, name="dashboard")]
