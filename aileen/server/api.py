import logging

from data.models import SeenByDay, SeenByHour, UniqueDevices
from data.queries import prepare_df_datetime_index
from django.core.serializers import deserialize
from django.db import transaction
from django.http import (HttpResponse, HttpResponseBadRequest,
                         HttpResponseForbidden, HttpResponseNotFound,
                         JsonResponse)
from django.views.decorators.csrf import csrf_exempt
from server.models import AileenBox

logger = logging.getLogger(__name__)


def box_data_receiver(func):
    """Decorator for post endpoints which receive data from boxes.
    Performs checks and wraps endpoint code in try/except handling and an atomic db transaction."""

    def wrapper(request, box_id):
        # check method
        if request.method not in ("POST", "PUT"):
            logger.warning(f"Got {request.method} request, only POST is allowed.")
            return HttpResponseBadRequest()

        # check authorization token
        if (
            request.META.get("HTTP_AUTHORIZATION") != "dummy-token"
        ):  # TODO: no hard-coding this, of course
            logger.warning(
                f"Client sent wrong HTTP_AUTHORIZATION header: {request.META.get('HTTP_AUTHORIZATION')}"
            )
            return HttpResponseForbidden()

        # check if box exists
        box = AileenBox.objects.filter(box_id=box_id).first()
        if box is None:
            logger.error(f"Box with id {box_id} could not be found.")
            return HttpResponseNotFound("No box")

        try:
            with transaction.atomic():
                func(request, box_id)
        except Exception as e:
            logger.error(str(e))
            return HttpResponseBadRequest(str(e))

        return HttpResponse(200)

    return wrapper


@csrf_exempt
@box_data_receiver
def post_events(request, box_id):
    """
    For boxes to upload raw event data.

    Expects JSON data for devices and events, like this:
    {"devices": [ ...], "events": [ ... ]}
    """

    logger.info(f"Got event data for Box {box_id}")

    # deserialize
    devices = list(deserialize("json", request.POST.get("devices", "[]")))
    logger.info(f"Received {len(devices)} devices.")
    events = list(deserialize("json", request.POST.get("events", {})))
    logger.info(f"Received {len(events)} events.")
    for device in devices:
        existing_device = UniqueDevices.objects.filter(
            device_id=device.object.device_id
        ).first()
        if (
            existing_device
            and existing_device.time_last_seen > device.object.time_last_seen
        ):
            device.object.time_last_seen = existing_device.time_last_seen
        device.save()

    for event in events:
        if event.object.box_id != box_id:
            raise Exception(
                f"Event with box_id {event.object.box_id} was sent, while request box_id is {box_id}."
            )
        event.save()


@csrf_exempt
@box_data_receiver
def post_aggregations(request, box_id):
    """
    For boxes to upload aggregated event data.

    Expects JSON data for seen by hour and seen by day, like this:
    {"seen_by_hour": [ ...], "seen_by_day": [ ... ]}
    """

    logger.info(f"Got aggregation data for Box {box_id}")

    seen_by_hour = list(deserialize("json", request.POST.get("seen_by_hour", "[]")))
    logger.info(f"Received {len(seen_by_hour)} hourly aggregations.")
    seen_by_day = list(deserialize("json", request.POST.get("seen_by_day", "[]")))
    logger.info(f"Received {len(seen_by_day)} daily aggregations.")

    for sb in seen_by_hour + seen_by_day:
        if sb.object.box_id != box_id:
            raise Exception(
                f"SeenByHour with box_id {sb.object.box_id} was sent, while request box_id is {box_id}."
            )
        sb.save()


@csrf_exempt
@box_data_receiver
def post_tmux_status(request, box_id):
    """
    For boxes to upload TmuxStatus data.

    Expects JSON data for airodump_ng status, like this:
    {"tmux_statuss": [...]}
    """
    logger.info(f"Got TmuxStatus data for Box {box_id}")

    # deserialize
    tmux_statuss = list(deserialize("json", request.POST.get("tmux_statuss", "[]")))
    logger.info(f"Received {len(tmux_statuss)} tmux statuss'.")
    for status in tmux_statuss:
        if status.object.box_id != box_id:
            raise Exception(
                f"Status with box_id {status.object.box_id} was send, while request box_id is {box_id}."
            )
        status.save()


# home
def average_number_of_devices_seen_by_box(request):
    """
    For D3 bar graph
    """
    boxes = [
        row["box_id"] for row in SeenByDay.objects.values("box_id").distinct().all()
    ]

    box_info_list = []
    for box_id in boxes:
        box = AileenBox.objects.filter(box_id=box_id).first()
        if box is not None:
            box_info = dict(box_name=None, mean_devices_each_day=None)
            box_info["box_name"] = box.name
            box_info["mean_devices_each_day"] = box.average_devices_per_day
            box_info_list.append(box_info)

    return JsonResponse(box_info_list, safe=False)
