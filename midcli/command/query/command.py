# -*- coding=utf-8 -*-
import logging

from midcli.command.call_mixin import CallMixin
from midcli.command.interface import Command

from .completions import get_completions
from .parse import ParseError, parse

logger = logging.getLogger(__name__)

__all__ = ["QueryCommand"]


class QueryCommand(CallMixin, Command):
    def __init__(self, *args, method=None, **kwargs):
        self.method = method
        super().__init__(*args, **kwargs)

    def process_input(self, text):
        try:
            parsed = parse(text or "")
        except ParseError as e:
            print(e.args[0])
            return

        self.call(self.method["name"], parsed.filters, parsed.options)

    def get_completions(self, text):
        return get_completions(self.method["filterable_schema"], text)
