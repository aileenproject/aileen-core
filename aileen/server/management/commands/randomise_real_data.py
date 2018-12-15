from math import floor
from datetime import datetime, timedelta
import os

import pandas as pd
import numpy as np

from django.db import transaction
from django.core.management.base import BaseCommand
from django.conf import settings
from data.models import SeenByHour, SeenByDay



data_dir = os.path.join(settings.BASE_DIR, 'data/dummy_data/')

seen_by_hour = os.path.join(data_dir, 'seenbyhour.csv')
seen_by_day  = os.path.join(data_dir, 'seenbyday.csv')

def randomizeRow(df_row: int):
    return int(np.random.normal(df_row, df_row * 0.2, 1))


def generate_random_data(options: dict):

    number_of_iterations = options['number_of_iterations']
    box_id = options['box_id']

    df = pd.read_csv(seen_by_hour)
    day_df = pd.read_csv(seen_by_day)

    df = df[df.seen != 0]
    df.drop(["Unnamed: 0", "id", "box_id"], axis=1, inplace=True)

    number_of_counted_hours = len(df)

    whole_days = floor(number_of_counted_hours / 24)
    df = df.head(whole_days * 24)
    df.reset_index(inplace=True)

    hourly = []
    for iteration in range(number_of_iterations):
        for index, row in df.iterrows():
            seen = randomizeRow(row["seen"])
            seen_also_in_preceding_hour = randomizeRow(row["seen_also_in_preceding_hour"])
            hour_start = pd.Timestamp(row["hour_start"]) + timedelta(
                hours= whole_days * 24 * iteration
            )
            hourly.append(
                SeenByHour(
                        hour_start=hour_start,
                        seen=seen,
                        seen_also_in_preceding_hour=seen_also_in_preceding_hour,
                        box_id=box_id
                )
            )

    daily = []
    for itteration in range(number_of_iterations):
        for index, row in day_df.iterrows():
            daily.append(
                SeenByDay(
                    box_id=box_id,
                    day_start= pd.Timestamp(row['day_start']) + timedelta(hours= whole_days * 24 * iteration),
                    seen=randomizeRow(row['seen']),
                    seen_also_on_preceding_day=int(
                        randomizeRow(row['seen_also_on_preceding_day'])
                    ),
                    seen_also_a_week_earlier=int(
                        randomizeRow(row['seen_also_a_week_earlier'])
                    ),
                )
            )

    with transaction.atomic():
        for aggregation in hourly + daily:
            aggregation.save()



class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--box_id', type=str)
        parser.add_argument('--number_of_iterations', type=int, default=40)

    def handle(self, *args, **options):
        generate_random_data(options)
