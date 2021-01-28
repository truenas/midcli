# -*- coding=utf-8 -*-
from prompt_toolkit.completion import Completion
import pytest

from midcli.command.query.completions import get_completions

USER_FILTERABLE_SCHEMA = {
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
}


def fields_for(prefix, exclude=None):
    exclude = exclude or []

    return [
        Completion(name, -len(prefix))
        for name in USER_FILTERABLE_SCHEMA["_attrs_order_"]
        if name.startswith(prefix) and name not in exclude
    ]


@pytest.mark.parametrize("text,completions", [
    ("", fields_for("")),
    ("u", fields_for("u")),
    ("up", []),
    ("uid,", fields_for("", exclude=["uid"])),
    ("uid,u", fields_for("u", exclude=["uid"])),
    ("uid,u ", [Completion("WHERE", 0)]),
    ("uid,username", []),
    ("uid,username ", [Completion("WHERE", 0)]),
    ("uid,username WHERE", []),
    ("uid,username WHERE ", fields_for("")),
    ("uid,username WHERE u", fields_for("u")),
    ("uid,username WHERE uid ", []),
    ("uid,username WHERE uid >", []),
    ("uid,username WHERE uid > ", []),
    ("uid,username WHERE uid > 6", []),
    ("uid,username WHERE uid > 6 ", []),
    ("uid,username WHERE uid > 6 a", []),
    ("uid,username WHERE uid > 6 and", []),
    ("uid,username WHERE uid > 6 and ", fields_for("")),
    ("uid,username WHERE uid > 6 and u", fields_for("u")),
    ("uid,username WHERE (", fields_for("")),
    ("uid,username WHERE (u", fields_for("u")),
    ("*", [Completion(" WHERE", 0)]),
    ("* ", [Completion("WHERE", 0)]),
    ("#", []),
])
def test_autocomplete(text, completions):
    assert get_completions(USER_FILTERABLE_SCHEMA, text) == completions
