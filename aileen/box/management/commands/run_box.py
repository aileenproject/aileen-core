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
        logger.error(
            "%s No box settings found. Please add from the admin panel."
            % settings.TERM_LBL
        )
        sys.exit(2)

    if settings.SENSOR_MODULE == "":
        logger.error("%s The AILEEN_SENSOR_MODULE setting is not set!" % settings.TERM_LBL)
        sys.exit(2)
    logger.info(
        f"{settings.TERM_LBL} Using {settings.SENSOR_MODULE} as the sensor module ..."
    )

    sensor = get_sensor()  # this checks if import went well
    if hasattr(sensor, "check_preconditions"):
        sensor.check_preconditions()

    if settings.HASH_OBSERVABLE_IDS is False:
        logger.warning("%s AILEEN_HASH_OBSERVABLE_IDS is False!" % settings.TERM_LBL)


def start_sensor_in_tmux(tmux_session, new_window: bool = False):
    tmp_dir = build_tmp_dir_name()
    logger.info(f"{settings.TERM_LBL} Starting the sensor ...")
    cmd = (
        '%s%s -c \'import importlib; sensor=importlib.import_module("%s"); sensor.start_sensing("%s")\''
        % (
            "%s " % settings.ACTIVATE_VENV_CMD
            if settings.ACTIVATE_VENV_CMD is not None
            else "",
            sys.executable,
            settings.SENSOR_MODULE,
            tmp_dir,
        )
    )

    run_command_in_tmux(
        tmux_session,
        cmd,
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

    start_sensor_in_tmux(tmux_session, new_window=False)

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
        "%s Starting to record data to the local db at %s ..."
        % (settings.TERM_LBL, settings.DATABASES["default"].get("NAME"))
    )

    # now start the data aggregation
    run_command_in_tmux(
        tmux_session,
        "%s %s manage.py aggregate_data" % (settings.ACTIVATE_VENV_CMD, sys.executable),
        restart_after_n_seconds=3,
        window_name="aggregate_data",
    )
    logger.info("%s Starting to aggregate data ..." % settings.TERM_LBL)
    time.sleep(2)

    # now start to monitor tmux
    run_command_in_tmux(
        tmux_session,
        "%s %s manage.py monitor_tmux" % (settings.ACTIVATE_VENV_CMD, sys.executable),
        restart_after_n_seconds=3,
        window_name="monitor_tmux",
    )
    logger.info(
        "%s Monitoring all of the running tmux sessions ..." % settings.TERM_LBL
    )

    # Starting the local dashboard server - needs sudo rights if the port is 80
    if int(settings.BOX_PORT) == 80:
        command = (
            f"echo {sudo_password} | sudo -S {settings.ACTIVATE_VENV_CMD} {sys.executable}"
            f" manage.py runserver 0.0.0.0:{str(settings.BOX_PORT)}"
        )
    else:
        command = f"{settings.ACTIVATE_VENV_CMD} {sys.executable} manage.py runserver 0.0.0.0:{str(settings.BOX_PORT)}"
    run_command_in_tmux(
        tmux_session, command, restart_after_n_seconds=3, window_name="local_dashboard"
    )
    logger.info("%s Starting the local dashboard server ..." % settings.TERM_LBL)

    if not settings.INTERNET_CONNECTION_AVAILABLE:
        logger.info(
            "%s INTERNET_CONNECTION_AVAILABLE is false, so data is not being uploaded."
            % settings.TERM_LBL
        )
        return

    # now start the data uploader
    run_command_in_tmux(
        tmux_session,
        "%s %s manage.py upload_data" % (settings.ACTIVATE_VENV_CMD, sys.executable),
        restart_after_n_seconds=3,
        window_name="upload_data",
    )
    box_settings = BoxSettings.objects.first()
    logger.info(
        "%s Starting to upload data against %s ..."
        % (settings.TERM_LBL, box_settings.server_url)
    )


class Command(BaseCommand):
    help = "Starts the process of detecting devices and upload the data."

    def handle(self, *args, **kwargs):
        if int(settings.BOX_PORT) != 80:
            run_box()
        else:
            run_box(
                sudo_password=getpass(
                    "Sudo password (required to run local server on port 80):"
                )
            )
