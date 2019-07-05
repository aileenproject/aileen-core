import logging
import uuid
from typing import Optional

from django.core.management.base import BaseCommand
from django.db import transaction

from server.models import AileenBox

logger = logging.getLogger(__name__)


def make_new_aileenbox(options: dict) -> AileenBox:
    """ make a new aileen_box """
    aileen_box = None
    if options["id"] is None:
        options["id"] = uuid.uuid4()
    try:
        coordinates = [float(l) for l in options["location"].split(",")]
    except Exception as e:
        raise Exception("Location cannot be parsed: %s" % str(e))
    if options.get("name", "") == "":
        raise Exception("Name cannot be empty!")
    if options.get("description", "") == "":
        raise Exception("Description cannot be empty!")
    if AileenBox.objects.filter(box_id=options["id"]).first() is not None:
        raise Exception("Box with id %s already exists!" % options["id"])
    aileen_box = AileenBox(
        geom={"type": "Point", "coordinates": coordinates},
        box_id=options["id"],
        name=options["name"],
        description=options["description"],
    )
    return aileen_box


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
            "--location",
            nargs="?",
            type=str,
            default="4.925,52.393",
            help="Latitude and longitude for the box, separated by a comma.",
        )
        parser.add_argument(
            "--name", nargs="?", type=str, default="", help="Name of the box."
        )
        parser.add_argument(
            "--description",
            nargs="?",
            type=str,
            default="",
            help="Short description of the box.",
        )

    def handle(self, *args, **options):

        aileen_box = make_new_aileenbox(options)

        logger.info(
            "Created new Aileen box %s, name: '%s', description '%s' and location %s "
            % (
                aileen_box.box_id,
                aileen_box.name,
                aileen_box.description,
                aileen_box.geom,
            )
        )

        # Now save to the database
        with transaction.atomic():
            if aileen_box is not None:
                aileen_box.save()
