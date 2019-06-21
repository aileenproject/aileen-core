from django.shortcuts import render

from box.models import BoxSettings
from data.models import TmuxStatus
from data.queries import compute_kpis


def dashboard(request):

    try:
        airodump_ng_status = TmuxStatus.objects.last().airodump_ng
    except:
        airodump_ng_status = "No status available"

    box_id = BoxSettings.objects.last().box_id

    kpis = compute_kpis(box_id)
    # customise the kpis
    kpis["busyness"]["by_hour"]["num_observables"] = int(
        kpis["busyness"]["by_hour"]["num_observables"]
    )
    kpis["busyness"]["by_day"]["num_observables"] = int(
        kpis["busyness"]["by_day"]["num_observables"]
    )

    context = {"kpis": kpis, "airodump_ng_status": airodump_ng_status}
    template = "box/dashboard.html"
    return render(request, template, context)
