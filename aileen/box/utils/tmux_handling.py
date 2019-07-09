import logging
from subprocess import call
from typing import Callable

import libtmux
from django.conf import settings


logger = logging.getLogger(__name__)


def start_tmux_session(
    session_name: str, kill_existing=True, cleanup_func: Callable = None
) -> libtmux.Session:
    """start a tmux server"""
    server = libtmux.Server()
    if kill_existing and server.has_session(session_name):
        logger.info(
            '%s Killing the running tmux session "%s" ...'
            % (settings.TERM_LBL, session_name)
        )
        kill_tmux_session(session_name)
    if cleanup_func is not None:
        logger.info(
            "%s Cleaning up by calling %s ..."
            % (settings.TERM_LBL, cleanup_func.__name__)
        )
        cleanup_func()
    logger.info(
        '%s Starting new tmux session "%s" ...' % (settings.TERM_LBL, session_name)
    )
    return server.new_session(session_name=session_name)


def kill_tmux_session(session_name: str):
    """Find and kill this session"""
    server = libtmux.Server()
    if server and server.has_session(session_name):
        logger.info(
            '%s Killing the running tmux session "%s" ...'
            % (settings.TERM_LBL, session_name)
        )
    call(["tmux", "kill-session", "-t", session_name])


def run_command_in_tmux(
    session: libtmux.Session,
    cmd: str,
    new_window: bool = True,
    restart_after_n_seconds: int = -1,
    window_name=None,
):
    """
    Run command in a tmux session.
    if new_window is True, a new window is opened first and the command is run there.
    """
    if new_window:
        window = session.new_window(attach=False, window_name=window_name)
    else:
        window = session.list_windows()[0]
        window.rename_window(window_name)

    if restart_after_n_seconds >= 0:
        cmd = (
            'result=1; while true; do echo "sleeping a bit..." ; sleep %d; '
            ' %s; result=$?; echo "Error code is $result"; done;'
            % (restart_after_n_seconds, cmd)
        )

    window.select_pane("0").send_keys(cmd, enter=True)
    logger.debug('%s Command "%s" started' % (settings.TERM_LBL, cmd))


if __name__ == "__main__":
    logger.info("%s Starting a test tmux session ..." % settings.TERM_LBL)
    new_session = start_tmux_session("test")

    run_command_in_tmux(
        session=new_session,
        cmd="python -c 'import time; while True: print(\"Test\"); time.sleep(2)'",
        new_window=False,
    )

    kill_tmux_session("test")
