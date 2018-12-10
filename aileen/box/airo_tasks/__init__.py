import logging
import os
import sys

from django.conf import settings
from box.utils.tmux_handling import run_command_in_tmux
from box.utils.dir_handling import build_tmp_dir_name
from box.airo_tasks.start_airodump import find_interface, run_with_sudo


logger = logging.getLogger(__name__)


def run_airodump_in_tmux(tmux_session, sudo_password, new_window=False):
    airodump_params = (
        "--sudo-pwd %s --airmon-ng-path %s --airodump-path %s --airodump-file-prefix %s"
        " --wifi-interfaces %s --airodump-log-interval-in-seconds %d"
        % (
            sudo_password,
            settings.FULL_PATH_TO_AIRMON_NG,
            settings.FULL_PATH_TO_AIRODUMP,
            os.path.join(build_tmp_dir_name(), settings.AIRODUMP_FILE_PREFIX),
            settings.WIFI_INTERFACES,
            settings.AIRODUMP_LOG_INTERVAL_IN_SECONDS,
        )
    )
    run_command_in_tmux(
        tmux_session,
        "%s %s/box/airo_tasks/start_airodump.py %s"
        % (sys.executable, settings.BASE_DIR, airodump_params),
        new_window=new_window,
        restart_after_n_seconds=3,
        window_name="airodump-ng",
    )
    logger.info(
        "Started airodump listening on %s ..."
        % find_interface(settings.WIFI_INTERFACES)
    )
