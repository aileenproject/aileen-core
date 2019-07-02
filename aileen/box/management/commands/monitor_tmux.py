import logging
import os
import time
from datetime import datetime

import pytz
from django.conf import settings
from django.core.management.base import BaseCommand

import libtmux
from box.management.commands.run_box import start_sensor_in_tmux
from box.models import BoxSettings
from box.utils.dir_handling import build_tmp_dir_name
from data.models import TmuxStatus
from data.time_utils import sleep_until_interval_is_complete

"""
This command is concerned with the health of tmux sessions. State is monitored and periodic restarts are done.
Currently, this concerns only the sensor, but add any other handling here as necessary (state is of interest on the
server, or periodic restarts would improve stability).
"""

logger = logging.getLogger(__name__)


def restart_sensor(tmux_session, sudo_pwd: str = None):
    """Kill the tmux window running the sensor, delete all sensor files, and start fresh."""
    logger.info("Restarting sensor for long-term health and sanitary reasons ...")
    tmux_session.find_where({"window_name": "sensor"}).kill_window()
    tmp_dir = build_tmp_dir_name()
    for sensor_file in [
        f for f in os.listdir(tmp_dir) if f.startswith(settings.SENSOR_FILE_PREFIX)
    ]:
        os.remove(f"{tmp_dir}/{sensor_file}")
    start_sensor_in_tmux(tmux_session, sudo_pwd, new_window=True)


def monitor_tmux_windows(tmux_session):
    """Monitor if tmux windows are doing fine. For now, only the sensor, can add others later."""
    box_id = BoxSettings.objects.last().box_id
    timezone = pytz.timezone(settings.TIME_ZONE)

    status = True  # start optimistic

    tmux_window = tmux_session.find_where({"window_name": "sensor"})
    if tmux_window is None:
        status = False
        logger.info(
            "Cannot find the \"sensor\" tmux window. Assuming sensor is not running..."
        )

    tmux_pane = tmux_window.list_panes()[0]
    last_message = tmux_pane.cmd("capture-pane", "-p").stdout[-1]

    if last_message == "sleeping a bit...":
        status = False
        logger.info(
            "The sensor seems to be off (process is sleeping and will try again) ..."
        )

    TmuxStatus.objects.update_or_create(
        box_id=box_id,
        sensor_status=status,
        time_stamp=timezone.localize(datetime.now()),
    )


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--sudo-pwd",
            nargs="?",
            type=str,
            help="The sudo password, if necessary, to restart the sensor.",
        )

    def handle(self, *args, sudo_pwd=None, **kwargs):
        tmux_server = libtmux.Server()
        tmux_session = tmux_server.find_where(
            {"session_name": settings.TMUX_SESSION_NAME}
        )
        restart_frequency = (
            settings.PROCESS_RESTART_INTERVAL_IN_SECONDS
            / settings.STATUS_MONITORING_INTERVAL_IN_SECONDS
        )
        logger.info(
            "I will restart processes after %d status check(s)..." % restart_frequency
        )
        monitoring_count = 0
        if sudo_pwd == "":
            sudo_pwd = None

        while True:
            start_time = time.time()

            monitor_tmux_windows(tmux_session)
            sleep_until_interval_is_complete(
                start_time, settings.STATUS_MONITORING_INTERVAL_IN_SECONDS
            )
            monitoring_count += 1

            if monitoring_count == restart_frequency:
                restart_sensor(tmux_session, sudo_pwd)
                monitoring_count = 0

            print()
