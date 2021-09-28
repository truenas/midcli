# -*- coding=utf-8 -*-
import functools
import logging

from midcli.command.call_mixin import CallMixin
from midcli.command.interface import Command, ProcessInputError

from .completions import get_completions
from .parse import ParseError, parse

logger = logging.getLogger(__name__)

__all__ = ["QueryCommand"]


def output_processor(select, rv):
    if select is not None:
        if isinstance(rv, dict):
            return {k: v for k, v in rv.items() if k in select}

        if isinstance(rv, list):
            return [output_processor(select, item) for item in rv]

    return rv


class QueryCommand(CallMixin, Command):
    def __init__(self, *args, method=None, **kwargs):
        self.method = method
        super().__init__(*args, **kwargs)

    def process_input(self, text):
        try:
            parsed = parse(text or "")
        except ParseError as e:
            raise ProcessInputError(e.args[0])

        select = parsed.options.pop("select", None)

        self.call(self.method["name"], parsed.filters, parsed.options,
                  output_processor=functools.partial(output_processor, select))

    def get_completions(self, text):
        return get_completions(self.method["filterable_schema"], text)
