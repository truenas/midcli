# -*- coding=utf-8 -*-
from unittest.mock import Mock

from prompt_toolkit.completion import Completion
import pytest

from midcli.command.common_syntax.argument import Argument
from midcli.utils.lang import undefined


@pytest.mark.parametrize("kwargs_override,values,text,completions", [
    ({}, ["ON", "OFF"], "", ["ON", "OFF"]),
    ({}, ["ON", "OFF"], "O", ["ON", "OFF"]),
    ({}, ["ON", "OFF"], "OF", ["OFF"]),
    ({}, ["ON", "OFF"], '"O', ['"ON"', '"OFF"']),
    ({"nullable": True}, ["ON", "OFF"], '', ["ON", "OFF", "null"]),
    ({"nullable": True}, ["ON", "OFF"], "O", ["ON", "OFF"]),
    ({"nullable": True}, ["ON", "OFF"], '\"', ['"ON"', '"OFF"']),
    ({"default": "ON"}, [], "", ["ON"]),
    ({"default": None, "nullable": True}, [], "", ["null"]),
    ({"default": None, "nullable": True}, [None], "", ["null"]),
])
def test_enum_argument_get_completions(kwargs_override, values, text, completions):
    kwargs = {
        "name": "name",
        "nullable": False,
        "default": undefined,
    }
    kwargs.update(kwargs_override)
    argument = Argument(**kwargs)
    argument.get_completions_values = Mock(return_value=values)
    assert list(argument.get_completions(text)) == [Completion(v, -len(text)) for v in completions]
