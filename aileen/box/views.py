from django.shortcuts import render

from data.queries import compute_kpis
from data.models import TmuxStatus
from box.models import BoxSettings


def dashboard(request):

    try:
        airodump_ng_status = TmuxStatus.objects.last().airodump_ng
    except:
        airodump_ng_status = "No status available"

    box_id = BoxSettings.objects.last().box_id

    kpis = compute_kpis(box_id)
    # customise the kpis
    kpis["busyness"]["by_hour"]["num_devices"] = int(
        kpis["busyness"]["by_hour"]["num_devices"]
    )
    kpis["busyness"]["by_day"]["num_devices"] = int(
        kpis["busyness"]["by_day"]["num_devices"]
    )

    context = {"kpis": kpis, "airodump_ng_status": airodump_ng_status}
    template = "box/dashboard.html"
    return render(request, template, context)
