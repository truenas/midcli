# -*- coding=utf-8 -*-
import logging

from midcli.command.interface import Command
from midcli.utils.shell import spawn_shell

logger = logging.getLogger(__name__)

__all__ = ["ShellCommand"]


class ShellCommand(Command):
    builtin = True
    hidden = True
    name = "shell"
    description = "Switch to shell"

    def process_input(self, text):
        spawn_shell()
