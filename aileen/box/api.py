from django.http import JsonResponse

from data.models import UniqueDevices, DevicesEvents
from data.queries import (
    prepare_df_datetime_index,
    unique_devices_per_bin_size,
    data_from_selected_device,
    data_for_device_per_unit_time,
)
from data.models import SeenByHour


def devices(request):
    """
    FOR D3
    Returns a list of dictionaries containing the following
    [{'time': '2018-11-15 16:00:00', 'devices': 115},{...}]
    """
    if request.method == "GET":
        box_id = str(request).split("?=")[-1].replace("'>", "")

        seen_by_hour_df = prepare_df_datetime_index(
            SeenByHour.pdobjects.to_dataframe(
                fieldnames=["hour_start", "seen", "seen_also_in_preceding_hour"]
            ),
            time_column="hour_start",
        )
        seen_by_hour_df = seen_by_hour_df.reset_index().rename(
            columns={"seen": "devices"}
        )
        seen_by_hour_df["time"] = seen_by_hour_df["time"].map(
            lambda x: x.strftime("%s")
        )

        data = seen_by_hour_df.to_dict("records")

    return JsonResponse(data, safe=False)
