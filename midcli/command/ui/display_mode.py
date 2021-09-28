# -*- coding=utf-8 -*-
import logging

from midcli.command.interface import Command, ProcessInputError

logger = logging.getLogger(__name__)

__all__ = ["ModeCommand"]


class ModeCommand(Command):
    builtin = True
    hidden = True
    name = ".mode"
    description = "Get/set output mode"

    def process_input(self, text):
        if not text:
            print("Current output mode: %s" % self.context.display_mode_manager.mode_name)
            return

        try:
            self.context.display_mode_manager.set_mode(text)
        except ValueError as e:
            raise ProcessInputError(f"Error: {e.args[0]}")
