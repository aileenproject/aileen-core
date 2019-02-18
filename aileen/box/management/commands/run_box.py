import logging
import sys
import time
from getpass import getpass

from django.conf import settings
from django.core.management.base import BaseCommand

from box.airo_tasks import run_airodump_in_tmux
from box.airo_tasks.start_airodump import find_interface
from box.models import BoxSettings
from box.utils.dir_handling import clean_tmp_files
from box.utils.tmux_handling import run_command_in_tmux, start_tmux_session

logger = logging.getLogger(__name__)


def check_preconditions():
    """Check necessary preconditions before we start anything."""
    if BoxSettings.objects.count() == 0:
        logger.error("No box settings found. Please add from the admin panel.")
        sys.exit(2)

    # check if we can find the network interface to monitor
    find_interface(settings.WIFI_INTERFACES)

    if settings.HASH_MAC_ADDRESSES is False:
        logger.warning("HASH_MAC_ADDRESSES is False!")


def run_box(sudo_password: str):
    """
    Start the tools necessary to detect clients and upload the data in tmux sessions.

    One session runs airodump, another transfers its output to the Aileen database. The third session uploads.
    We're attempting to keep running even in bad situations, so we restart the first two commands after 3 seconds
    if they fail for any reason. The upload command will remember what could be uploaded successfully and retry from
    the last success otherwise.
    The sudo password is currently needed to run airodump.
    TODO: One could also add it to commands that do not need that.
    """

    check_preconditions()

    tmux_session = start_tmux_session(
        settings.TMUX_SESSION_NAME, cleanup_func=clean_tmp_files
    )

    logger.info(f"{settings.TERM_LBL} Starting the airodump tool ...")

    run_airodump_in_tmux(tmux_session, sudo_password)

    # now start putting event data into the db
    time.sleep(settings.AIRODUMP_LOG_INTERVAL_IN_SECONDS / 4)
    run_command_in_tmux(
        tmux_session,
        "%s %s manage.py record_events_to_db"
        % (settings.ACTIVATE_VENV_CMD, sys.executable),
        restart_after_n_seconds=3,
        window_name="record_events_to_db",
    )
    logger.info(
        "Starting to record data to the local db at %s ..."
        % settings.DATABASES["default"].get("NAME")
    )

    command = (
        f"echo {sudo_password} | sudo -S {settings.ACTIVATE_VENV_CMD} {sys.executable}"
        f" manage.py runserver 0.0.0.0:{str(settings.BOX_PORT)}"
    )
    run_command_in_tmux(
        tmux_session, command, restart_after_n_seconds=3, window_name="local_dashboard"
    )
    logger.info("Starting the local dashboard server ...")

    # now start the data aggregation
    run_command_in_tmux(
        tmux_session,
        "%s %s manage.py aggregate_data" % (settings.ACTIVATE_VENV_CMD, sys.executable),
        restart_after_n_seconds=3,
        window_name="aggregate_data",
    )
    logger.info("Starting to aggregate data ...")
    time.sleep(2)

    # now start the data uploader
    run_command_in_tmux(
        tmux_session,
        "%s %s manage.py upload_data" % (settings.ACTIVATE_VENV_CMD, sys.executable),
        restart_after_n_seconds=3,
        window_name="upload_data",
    )
    box_settings = BoxSettings.objects.first()
    logger.info("Starting to upload data against %s ..." % box_settings.server_url)

    # now start to monitor tmux
    run_command_in_tmux(
        tmux_session,
        "%s %s manage.py monitor_tmux --sudo-pwd %s"
        % (settings.ACTIVATE_VENV_CMD, sys.executable, sudo_password),
        restart_after_n_seconds=3,
        window_name="monitor_tmux",
    )
    logger.info("Monitoring all of the running tmux sessions")


class Command(BaseCommand):
    help = "Starts the process of detecting devices and upload the data."

    def handle(self, *args, **kwargs):
        if settings.SUDO_PWD is not None and settings.SUDO_PWD != "":
            run_box(settings.SUDO_PWD)
        else:
            run_box(getpass("sudo password:"))
