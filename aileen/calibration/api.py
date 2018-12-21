from data.models import UniqueDevices
from data.queries import (data_for_device_per_unit_time,
                          data_from_selected_device)
from django.http import JsonResponse


def device_per_unit_time(request, *args, **kwargs):
    """
    FOR D3
    Returns a list of dictionaries containing the following
    [{'time': '2018-11-18 15:00:00', 'device_power': 31.0, 'seen_count': 48.0, 'packets_captured': 287.0},{...}]
    """
    device_id = str(request).split("?=")[-1].replace("-", ":").replace("'>", "")

    data = data_for_device_per_unit_time(device_id)
    return JsonResponse(data, safe=False)


def selected_device(request, *args, **kwarts):
    """
    FOR TABLE
    Used to gather data on a single device through a get request from the client
    the client requests the data for a single device, it comes through the url
    the url is then parsed and a json response is generated with the following:
    [{'device_power':device_power, 'time_seen':time_seen,
      'access_point_id':access_point_id, 'packets_captured',packets_captured}, {...}]
    """
    device_id = str(request).split("=")[-1].replace("-", ":").replace("'>", "")

    df = data_from_selected_device(device_id)
    df.drop("box_id", 1, inplace=True)

    data = df.to_dict("records")
    return JsonResponse(data, safe=False)
