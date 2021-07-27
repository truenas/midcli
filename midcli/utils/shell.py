# -*- coding=utf-8 -*-
import logging
import os
import sys

logger = logging.getLogger(__name__)

__all__ = ["is_main_cli", "switch_to_shell"]


def is_main_cli():
    # Returns true if we are the instance ran by systemd on primary terminal
    return os.getppid() == 1 or os.environ.get("_IS_MAIN_CLI") == "1"


def switch_to_shell():
    try:
        ttyname = os.ttyname(sys.stdout.fileno())
    except Exception as e:
        print(f"Failed to determine active tty: {e}")
        os.execv("/bin/login", ["/bin/login"])
    else:
        terminal = os.path.relpath(ttyname, "/dev")
        os.execv("/sbin/agetty", ["/sbin/agetty", "--noclear", "--keep-baud", terminal])
