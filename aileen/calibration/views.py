<<<<<<< HEAD
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
=======
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
>>>>>>> merging_with_nic

from data.models import UniqueDevices


def calibration(request):

    all_unique_devices = list(UniqueDevices.objects.values("device_id"))

    context = {"all_unique_devices": all_unique_devices, "page": "calibration"}

    template = "calibration/calibration.html"
    return render(request, template, context)
