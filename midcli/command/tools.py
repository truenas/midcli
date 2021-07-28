# -*- coding=utf-8 -*-
import logging
import os

from midcli.command.interface import Command

logger = logging.getLogger(__name__)

__all__ = ["ShellCommand"]


class ShellCommand(Command):
    builtin = True
    hidden = True
    name = "shell"
    description = "Switch to root shell"

    def process_input(self, text):
        os.system("/usr/bin/su -l root")
