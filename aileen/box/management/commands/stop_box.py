import logging

from box.utils.tmux_handling import kill_tmux_session
from django.conf import settings
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Stops the process of detecting devices and upload the data."

    def handle(self, *args, **kwargs):
        logger.info("stop_box command was called ...")
        kill_tmux_session(settings.TMUX_SESSION_NAME)
