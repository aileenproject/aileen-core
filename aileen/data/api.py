from django.http import JsonResponse
from django.http import HttpResponse

from data.models import SeenByHour
from data.queries import prepare_df_datetime_index
from data.queries import compute_kpis


def observables_by_box_id(request, box_id=None):
    """
    FOR D3
    Returns a list of dictionaries containing the following
    [{'time': '<tz-naive timestamp>', 'observables': 115},{...}]
    """
    seen_filter = SeenByHour.pdobjects
    if box_id is not None:
        seen_filter = seen_filter.filter(box_id=box_id)
    seen_by_hour_df = prepare_df_datetime_index(
        seen_filter.to_dataframe(
            fieldnames=["hour_start", "seen", "seen_also_in_preceding_hour"]
        ),
        time_column="hour_start",
    )

    seen_by_hour_df = seen_by_hour_df.reset_index().rename(
        columns={"seen": "observables"}
    )
    seen_by_hour_df["time"] = seen_by_hour_df["time"].map(
        lambda x: x.replace(tzinfo=None).timestamp()
    )

    data = seen_by_hour_df.to_dict("records")
    return JsonResponse(data, safe=False)


def observables(request):
    return observables_by_box_id(request, box_id=None)


def kpis_by_box_id(request, box_id):
    """
    returns the kpis by box id
    """
    try:
        kpis = compute_kpis(box_id)
        # customize the kpis

        kpis["running_since"] = ""
        kpis["observables_seen_per_day"] = int(kpis["observables_seen_per_day"])

        # by day
        kpis["busyness"]["by_day"]["num_observables"] = int(
            kpis["busyness"]["by_day"]["num_observables"]
        )
        kpis["busyness"]["by_day"]["percentage_margin_to_second"] = ""
        kpis["busyness"]["by_day"]["num_observables_mean"] = float(
            kpis["busyness"]["by_day"]["num_observables_mean"]
        )
        kpis["busyness"]["by_day"]["percentage_margin_to_mean"] = float(
            kpis["busyness"]["by_day"]["percentage_margin_to_mean"]
        )

        # by hour
        kpis["busyness"]["by_hour"]["num_observables"] = int(
            kpis["busyness"]["by_hour"]["num_observables"]
        )
        kpis["busyness"]["by_hour"]["hour_of_day"] = int(
            kpis["busyness"]["by_hour"]["hour_of_day"]
        )
        kpis["busyness"]["by_hour"]["percentage_margin_to_second"] = ""
        kpis["busyness"]["by_hour"]["num_observables_mean"] = float(
            kpis["busyness"]["by_hour"]["num_observables_mean"]
        )
        kpis["busyness"]["by_hour"]["percentage_margin_to_mean"] = float(
            kpis["busyness"]["by_hour"]["percentage_margin_to_mean"]
        )

    except:
        kpis = {"none": None}

    return JsonResponse(kpis)
