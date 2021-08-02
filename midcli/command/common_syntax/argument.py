# -*- coding=utf-8 -*-
import json
import logging

from prompt_toolkit.completion import Completion

from .parse import RE_SIMPLE_STRING

from midcli.utils.lang import undefined

logger = logging.getLogger(__name__)

__all__ = ["Argument", "BooleanArgument", "EnumArgument"]


class Argument:
    def __init__(self, name, nullable, default):
        self.name = name
        self.nullable = nullable
        self.default = default

    def get_completions(self, text):
        completions = self.get_completions_values().copy()
        if self.default != undefined and self.default not in completions:
            completions.append(self.default)
        if self.nullable and self.default is not None:
            completions.append(None)

        for value in completions:
            value = self._adapt_completion(value, text)
            if value.startswith(text):
                yield Completion(value, -len(text))

    def get_completions_values(self):
        return []

    def _adapt_completion(self, value, text):
        if isinstance(value, str) and RE_SIMPLE_STRING.match(value) and not text.startswith('"'):
            return value

        return json.dumps(value)


class BooleanArgument(Argument):
    def get_completions_values(self):
        return [True, False]


class EnumArgument(Argument):
    def __init__(self, *args, enum):
        super().__init__(*args)
        self.enum = enum

    def get_completions_values(self):
        if callable(self.enum):
            return self.enum()

        return self.enum
