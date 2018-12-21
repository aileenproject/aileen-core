from django.contrib import admin
from leaflet.admin import LeafletGeoAdmin
from server import models

admin.site.register(models.AileenBox, LeafletGeoAdmin)
