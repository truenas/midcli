# -*- coding=utf-8 -*-
import logging

from midcli.command.interface import Command

logger = logging.getLogger(__name__)

__all__ = ["StacksCommand"]


class StacksCommand(Command):
    builtin = True
    hidden = True
    name = ".stacks"
    description = "Enable/disable printing stack traces for errors"

    def process_input(self, text):
        if not text:
            print(f"Errors stack trace display: {'enabled' if self.context.stacks else 'disabled'}")
            return

        if text.lower() in ("0", "no", "off"):
            self.context.stacks = False
        elif text.lower() in ("1", "yes", "on"):
            self.context.stacks = True
        else:
            print(f"Invalid value: {text!r}. Should be 'on' or 'off'")
