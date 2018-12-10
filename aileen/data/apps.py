from django.apps import AppConfig


class DataConfig(AppConfig):
    name = "data"
    verbose_name = (
        "Data models shared between Aileen box and server code. Also access logic."
    )
