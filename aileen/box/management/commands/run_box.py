import logging
import sys
import time
import importlib
from getpass import getpass

from django.conf import settings
from django.core.management.base import BaseCommand

from box.models import BoxSettings
from box.utils.dir_handling import get_sensor, clean_tmp_files, build_tmp_dir_name
from box.utils.tmux_handling import run_command_in_tmux, start_tmux_session

logger = logging.getLogger(__name__)


def check_preconditions():
    """Check necessary preconditions before we start anything."""
    if BoxSettings.objects.count() == 0:
        logger.error("No box settings found. Please add from the admin panel.")
        sys.exit(2)

    if settings.SENSOR_MODULE == "":
        logger.error("The SENSOR_MODULE setting is not set!")
        sys.exit(2)
    logger.info(
        f"{settings.TERM_LBL} Using {settings.SENSOR_MODULE} as the sensor module ..."
    )

    sensor = get_sensor()  # this checks if import went well
    if hasattr(sensor, "check_preconditions"):
        sensor.check_preconditions()

    if settings.HASH_OBSERVABLE_IDS is False:
        logger.warning("HASH_OBSERVABLE_IDS is False!")


def start_sensor_in_tmux(
    tmux_session, sudo_password: str = None, new_window: bool = False
):
    tmp_dir = build_tmp_dir_name()
    logger.info(f"{settings.TERM_LBL} Starting the sensor ...")
    run_command_in_tmux(
        tmux_session,
        '%s %s%s -c \'import importlib; sensor=importlib.import_module("%s"); sensor.start_sensing("%s")\''
        % (
            settings.ACTIVATE_VENV_CMD,
            "%s " % sudo_password if sudo_password else "",
            sys.executable,
            settings.SENSOR_MODULE,
            tmp_dir,
        ),
        new_window=new_window,
        restart_after_n_seconds=3,
        window_name="sensor",
    )


def run_box(sudo_password: str = None):
    """
    Start the tools necessary to run the sensor and upload aggregated data in tmux sessions.

    One session runs the sensor (this might need sudo rights), another transfers
    its output to the Aileen database. The third session uploads.
    We're attempting to keep running even in bad situations, so we restart the first
    two commands after 3 seconds if they fail for any reason.
    The upload command will remember what could be uploaded successfully and otherwise
    retry from the last success.
    """

    check_preconditions()

    tmux_session = start_tmux_session(
        settings.TMUX_SESSION_NAME, cleanup_func=clean_tmp_files
    )

    start_sensor_in_tmux(tmux_session, sudo_password, new_window=False)

    # now start putting event data into the db
    time.sleep(settings.SENSOR_LOG_INTERVAL_IN_SECONDS / 4)
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

    # Starting the local dashboard server needs sudo rights if the port is 80
    if int(settings.BOX_PORT) == 80:
        command = (
            f"echo {sudo_password} | sudo -S {settings.ACTIVATE_VENV_CMD} {sys.executable}"
            f" manage.py runserver 0.0.0.0:{str(settings.BOX_PORT)}"
        )
    else:
        command = (
            f"{settings.ACTIVATE_VENV_CMD} {sys.executable} manage.py runserver 0.0.0.0:{str(settings.BOX_PORT)}"
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
        if not settings.SUDO_PWD_REQUIRED:
            run_box()
            return
        if settings.SUDO_PWD is not None and settings.SUDO_PWD != "":
            run_box(sudo_password=settings.SUDO_PWD)
        else:
            run_box(sudo_password=getpass("Sudo password (required to start sensor):"))
