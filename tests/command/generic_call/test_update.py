# -*- coding=utf-8 -*-
from unittest.mock import ANY, Mock

import pytest

from midcli.command.interface import ProcessInputError
from midcli.command.generic_call.update import UpdateCommand

USER_UPDATE = {
    "name": "user.update",
    "accepts": [
        {
            "_name_": "id",
            "_required_": True,
            "title": "User ID",
            "type": "integer",
        },
        {
            "_attrs_order_": ["uid", "username"],
            "_name_": "user_create",
            "properties": {
                "uid": {
                    "_name_": "uid",
                    "_required_": False,
                    "title": "Unix user ID",
                    "type": "integer",
                },
                "username": {
                    "_name_": "username",
                    "_required_": True,
                    "title": "Username",
                    "type": "string",
                },
            },
            "title": "update",
            "type": "object",
        },
    ],
    "job": False,
}


@pytest.mark.parametrize("text,is_interactive,call_args", [
    ("1000", True, [1000, {}]),
    ("id=1000", True, [1000, {}]),
    ("uid=1000", False, "Too few positional arguments (1 required, 0 given)"),
    ("id=1000 uid=1001", False, (1000, {"uid": 1001})),
    ("999 id=1000 uid=1001", False, (999, {"id": 1000, "uid": 1001})),
])
def test_update_call_args(text, is_interactive, call_args):
    command = UpdateCommand(Mock(), Mock(), "update", None, "user.update", method=USER_UPDATE, splice_kwargs=1)
    client = Mock()
    client.call.return_value = {}
    command.context = Mock()
    command.context.get_client.return_value = Mock(__enter__=Mock(return_value=client), __exit__=Mock())
    command._run_editor = Mock()
    command.call = Mock()

    if is_interactive:
        command.process_input(text)
        command._run_editor.assert_called_once_with(call_args, ANY, ANY, ANY)
    else:
        if isinstance(call_args, str):
            with pytest.raises(ProcessInputError) as e:
                command.process_input(text)

            command.call.assert_not_called()
            assert e.value.error == call_args
        else:
            command.process_input(text)
            command.call.assert_called_once_with("user.update", *call_args, job=False)
