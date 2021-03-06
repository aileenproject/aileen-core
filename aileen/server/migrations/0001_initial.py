# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2018-12-15 23:06
from __future__ import unicode_literals

import djgeojson.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="AileenBox",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("geom", djgeojson.fields.PointField()),
                ("box_id", models.CharField(max_length=256)),
                ("name", models.CharField(max_length=100)),
                ("description", models.TextField()),
            ],
            options={
                "verbose_name": "Aileen box",
                "verbose_name_plural": "Aileen boxes",
            },
        )
    ]
