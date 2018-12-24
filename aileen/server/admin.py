<<<<<<< HEAD
from django.contrib import admin
from leaflet.admin import LeafletGeoAdmin
=======
from leaflet.admin import LeafletGeoAdmin
from django.contrib import admin
>>>>>>> merging_with_nic

from server import models

admin.site.register(models.AileenBox, LeafletGeoAdmin)
