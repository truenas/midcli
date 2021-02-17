# -*- coding=utf-8 -*-
from unittest.mock import Mock

import pytest

from midcli.command.generic_call import GenericCallCommand

SCHEMA = {
    "name": "service.method",
    "accepts": [],
    "job": False,
}


@pytest.mark.parametrize("text,call_args", [
    ("", []),
])
def test_call_kwargs(text, call_args, capsys):
    command = GenericCallCommand(Mock(), Mock(), "create", None, "user.create", method=SCHEMA, splice_kwargs=None)
    command._run_interactive = Mock(side_effect=RuntimeError("Interactive run attempt"))
    command.call = Mock()
    command.process_input(text)
    if isinstance(call_args, str):
        command.call.assert_not_called()
        assert capsys.readouterr().out.rstrip() == call_args
    else:
        assert capsys.readouterr().out == ""
        command.call.assert_called_once_with("service.method", *call_args, job=False)
