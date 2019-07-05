import logging
import uuid

from django.core.management.base import BaseCommand
from django.db import transaction

from box.models import BoxSettings

logger = logging.getLogger(__name__)


def fill_box_settings(options: dict) -> BoxSettings:
    """ make new box settings if necessary, and fill them"""
    box_settings: BoxSettings = None
    if options["id"] is None:
        options["id"] = uuid.uuid4()
    if options.get("server_url", "") == "":
        raise Exception("server_url cannot be empty!")
    if options.get("upload_token", "") == "":
        raise Exception("upload_token cannot be empty!")
    if BoxSettings.objects.filter(box_id=options["id"]).first() is not None:
        raise Exception("Seetings for box id %s already exist!" % options["id"])
    box_settings = BoxSettings(
        box_id=options["id"],
        server_url=options["server_url"],
        upload_token=options["upload_token"],
    )
    return box_settings


class Command(BaseCommand):
    help = "Create a box. Could also happen via the admin panel."

    def add_arguments(self, parser):
        parser.add_argument(
            "--id",
            nargs="?",
            type=str,
            help="ID of box, If empty, a UUID will be created.",
        )
        parser.add_argument(
            "--server-url", nargs="?", type=str, default="", help="URL of the server."
        )
        parser.add_argument(
            "--upload-token",
            nargs="?",
            type=str,
            default="",
            help="Security token for uploading.",
        )

    def handle(self, *args, **options):

        box_settings = fill_box_settings(options)

        logger.info(
            "Filled box settings for box %s, server url: '%s', upload token '%s'"
            % (box_settings.box_id, box_settings.server_url, box_settings.upload_token)
        )

        # Now save to the database
        with transaction.atomic():
            if box_settings is not None:
                box_settings.save()
