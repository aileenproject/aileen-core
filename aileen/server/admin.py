from leaflet.admin import LeafletGeoAdmin
from django.contrib import admin

from server import models

admin.site.register(models.AileenBox, LeafletGeoAdmin)
