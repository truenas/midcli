# -*- coding=utf-8 -*-
from unittest.mock import Mock

import pytest

from midcli.command.interface import ProcessInputError
from midcli.command.generic_call import GenericCallCommand

SCHEMA = {
    "name": "service.method",
    "accepts": [
        {
            "_name_": "id",
        },
        {
            "_name_": "name",
        },
        {
            "_name_": "data",
        },
    ],
    "job": False,
}


@pytest.mark.parametrize("text,call_args", [
    ("1000", [1000]),
    ("id=1000", [1000]),
    ("name=ivan", "Missing positional argument 1 (id)"),
    ("1000 data={}", "Missing positional argument 2 (name)"),
    ("1000 nombre=juan", "Unknown keyword argument nombre"),
    ("1000 {} name=ivan", "Keyword argument name already given as positional argument 2"),
])
def test_call_kwargs(text, call_args):
    command = GenericCallCommand(Mock(), Mock(), "create", None, "user.create", method=SCHEMA, splice_kwargs=None)
    command._run_with_editor = Mock(side_effect=RuntimeError("Interactive run attempt"))
    command.call = Mock()
    if isinstance(call_args, str):
        with pytest.raises(ProcessInputError) as e:
            command.process_input(text)

        command.call.assert_not_called()
        assert e.value.error == call_args
    else:
        command.process_input(text)
        command.call.assert_called_once_with("service.method", *call_args, job=False)
