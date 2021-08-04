# -*- coding=utf-8 -*-
from unittest.mock import Mock

import pytest

from midcli.command.generic_call import GenericCallCommand

SCHEMA = {
    "name": "service.method",
    "accepts": [
        {
            "_name_": "interface",
            "type": "object",
            "properties": {
                "aliases": {
                    "type": "array",
                }
            }
        },
    ],
    "job": False,
}


@pytest.mark.parametrize("text,call_args", [
    ('{"aliases": 1000}', [{"aliases": [1000]}]),
    ('{"aliases": [1000, 1001]}', [{"aliases": [1000, 1001]}]),
    ('{"aliases": null}', [{"aliases": None}]),
    ('{}', [{}]),
])
def test_call_kwargs__single_value_to_list(text, call_args, capsys):
    command = GenericCallCommand(Mock(), Mock(), "create", None, "user.create", method=SCHEMA, splice_kwargs=None)
    command._run_with_editor = Mock(side_effect=RuntimeError("Interactive run attempt"))
    command.call = Mock()
    command.process_input(text)
    if isinstance(call_args, str):
        command.call.assert_not_called()
        assert capsys.readouterr().out.rstrip() == call_args
    else:
        assert capsys.readouterr().out == ""
        command.call.assert_called_once_with("service.method", *call_args, job=False)
