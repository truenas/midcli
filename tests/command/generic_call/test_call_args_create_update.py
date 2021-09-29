# -*- coding=utf-8 -*-
import copy
from unittest.mock import Mock

import pytest

from midcli.command.interface import ProcessInputError
from midcli.command.generic_call import GenericCallCommand

USER_CREATE = {
    "name": "user.create",
    "accepts": [
        {
            "_attrs_order_": ["uid", "username", "groups", "attributes"],
            "_name_": "user_create",
            "properties": {
                "attributes": {
                    "_attrs_order_": [],
                    "_name_": "attributes",
                    "_required_": False,
                    "additionalProperties": True,
                    "default": {},
                    "properties": {},
                    "title": "Additional attributes",
                    "type": "object",
                },
                "groups": {
                    "_name_": "groups",
                    "_required_": False,
                    "default": [],
                    "items": [{"type": "integer"}],
                    "title": "UNIX groups",
                    "type": "array",
                },
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
            "title": "user_create",
            "type": "object",
        },
    ],
    "job": False,
}

USER_UPDATE = copy.deepcopy(USER_CREATE)
USER_UPDATE["name"] = "user.update"
USER_UPDATE["accepts"].insert(0, {
    "_name_": "id",
    "_required_": True,
    "title": "User ID",
    "type": "integer",
})


@pytest.mark.parametrize("text,call_args", [
    ("1000", "Too many positional arguments (0 supported, 1 given)"),
    ("uid=1000", [{"uid": 1000}]),
    ('uid=1000 username="ivan"', [{"uid": 1000, "username": "ivan"}]),
])
def test_call_args_create(text, call_args,):
    command = GenericCallCommand(Mock(), Mock(), "create", None, "user.create", method=USER_CREATE, splice_kwargs=0)
    command._run_with_editor = Mock(side_effect=RuntimeError("Interactive run attempt"))
    command.call = Mock()
    if isinstance(call_args, str):
        with pytest.raises(ProcessInputError) as e:
            command.process_input(text)

        command.call.assert_not_called()
        assert e.value.error == call_args
    else:
        command.process_input(text)
        command.call.assert_called_once_with("user.create", *call_args, job=False)


@pytest.mark.parametrize("text,call_args", [
    ("55", [55, {}]),
    ("uid=1000", "Too few positional arguments (1 required, 0 given)"),
    ('55 uid=1000', [55, {"uid": 1000}]),
])
def test_call_args_update(text, call_args):
    command = GenericCallCommand(Mock(), Mock(), "update", None, "user.update", method=USER_UPDATE, splice_kwargs=1)
    command._run_with_editor = Mock(side_effect=RuntimeError("Interactive run attempt"))
    command.call = Mock()
    if isinstance(call_args, str):
        with pytest.raises(ProcessInputError) as e:
            command.process_input(text)

        command.call.assert_not_called()
        assert e.value.error == call_args
    else:
        command.process_input(text)
        command.call.assert_called_once_with("user.update", *call_args, job=False)
