from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.staticfiles.storage import staticfiles_storage
from django.views.generic.base import RedirectView

urlpatterns = [
    url(r"^admin/", admin.site.urls),
    url(
        r"^favicon.ico$",
        RedirectView.as_view(  # the redirecting function
            url=staticfiles_storage.url(
                "aileen/images/aileen.ico"
            )  # converts the static directory + our favicon into a URL
        ),
        name="favicon",
    ),
    url(r"^", include("data.urls", namespace="data")),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.AILEEN_MODE in ("server", "both"):
    urlpatterns.append(url(r"^", include("server.urls", namespace="server")))
elif settings.AILEEN_MODE == "box":
    urlpatterns.extend(
        (
            url(r"^", include("box.urls", namespace="box")),
            url(r"^", include("calibration.urls", namespace="calibration")),
        )
    )
