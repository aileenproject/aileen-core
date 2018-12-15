from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required

from server.models import AileenBox
from data.models import UniqueDevices, TmuxStatus
from data.queries import compute_kpis


class Landing(TemplateView):
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            return redirect("server:home")
        else:
            return redirect("server:login")


class Home(LoginRequiredMixin, TemplateView):
    template_name = "server/home.html"


@login_required
def box(request, box_id):

    # filter by box ID to get name
    box_name = AileenBox.objects.filter(box_id=box_id).get().name
    try:
        airodump_ng_status = TmuxStatus.objects.filter(box_id=box_id).last().airodump_ng
    except:
        airodump_ng_status = "No statis available"

    try:
        kpis = compute_kpis(box_id)
        # customise the kpis
        kpis["busyness"]["by_hour"]["num_devices"] = int(
            kpis["busyness"]["by_hour"]["num_devices"]
        )
        kpis["busyness"]["by_day"]["num_devices"] = int(
            kpis["busyness"]["by_day"]["num_devices"]
        )

        busiest_hour_range = f"{kpis['busyness']['by_hour']['hour_of_day']}:00-{kpis['busyness']['by_hour']['hour_of_day'] + 1}:00"

    except:
        kpis = {"none": None}
        busiest_hour_range = None

    # get the coordinates
    box_geom = AileenBox.objects.filter(box_id=box_id).get().geom
    box_coordinates = box_geom["coordinates"]

    context = {
        "box_name": box_name,
        "box_id": box_id,
        "box_coordinates": box_coordinates,
        "kpis": kpis,
        'busiest_hour_range':busiest_hour_range,
        "airodump_ng_status": airodump_ng_status,
    }

    template = "server/box.html"
    return render(request, template, context)