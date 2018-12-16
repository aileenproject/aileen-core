from django.http import JsonResponse

from data.models import SeenByHour
from data.queries import prepare_df_datetime_index


def devices_by_box_id(request, box_id):
    """
    FOR D3
    Returns a list of dictionaries containing the following
    [{'time': '<tz-naive timestamp>', 'devices': 115},{...}]
    """

    seen_by_hour_df = prepare_df_datetime_index(
        SeenByHour.pdobjects.filter(box_id=box_id).to_dataframe(
            fieldnames=["hour_start", "seen", "seen_also_in_preceding_hour"]
        ),
        time_column="hour_start",
    )

    seen_by_hour_df = seen_by_hour_df.reset_index().rename(columns={"seen": "devices"})
    seen_by_hour_df["time"] = seen_by_hour_df["time"].map(
        lambda x: x.replace(tzinfo=None).timestamp()
    )

    data = seen_by_hour_df.to_dict("records")
    print(data)
    return JsonResponse(data, safe=False)


def devices(request):
    seen_by_hour_df = prepare_df_datetime_index(
        SeenByHour.pdobjects.to_dataframe(
            fieldnames=["hour_start", "seen", "seen_also_in_preceding_hour"]
        ),
        time_column="hour_start",
    )
    seen_by_hour_df = seen_by_hour_df.reset_index().rename(columns={"seen": "devices"})

    seen_by_hour_df["time"] = seen_by_hour_df["time"].map(
        lambda x: x.replace(tzinfo=None).timestamp()
    )

    data = seen_by_hour_df.to_dict("records")
    print(data)
    return JsonResponse(data, safe=False)
