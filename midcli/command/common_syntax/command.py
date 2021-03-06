# -*- coding=utf-8 -*-
import logging

from prompt_toolkit.completion import Completion

from midcli.command.interface import Command

from .parse import AutocompleteName, AutocompleteValue, ParseError, parse_arguments, get_autocomplete

logger = logging.getLogger(__name__)

__all__ = ["CommonSyntaxCommand"]


class CommonSyntaxCommand(Command):
    arguments = []

    def process_input(self, text):
        try:
            args, kwargs = parse_arguments(text)
        except ParseError as e:
            print(e.args[0])
            return

        self.run(args, kwargs)

    def get_completions(self, text):
        autocomplete = get_autocomplete(text)

        if isinstance(autocomplete, AutocompleteName):
            for argument in self.arguments[autocomplete.args:]:
                if argument.name.startswith(autocomplete.name) and argument.name not in autocomplete.kwargs:
                    yield Completion(f"{argument.name}=", -len(autocomplete.name), argument.name)

        if isinstance(autocomplete, AutocompleteValue):
            for argument in self.arguments:
                if argument.name == autocomplete.name:
                    yield from argument.get_completions(autocomplete.value)

    def run(self, args, kwargs):
        raise NotImplementedError
