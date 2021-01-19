# -*- coding=utf-8 -*-
import errno
import textwrap
from unittest.mock import Mock

from midcli.editor.yaml.render import render_yaml

USER_CREATE_SCHEMA = {
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
                    "description": "Additional attributes",
                    "type": "object",
                },
                "groups": {
                    "_name_": "groups",
                    "_required_": False,
                    "default": [],
                    "items": [{"type": "integer"}],
                    "description": "UNIX groups",
                    "type": "array",
                },
                "uid": {
                    "_name_": "uid",
                    "_required_": False,
                    "description": "Unix user ID",
                    "type": "integer",
                },
                "username": {
                    "_name_": "username",
                    "_required_": True,
                    "description": "Username",
                    "type": "string",
                },
            },
            "description": "user_create",
            "type": "object",
        },
        {
            "_name_": "force",
            "_required_": False,
            "default": False,
            "description": "Force user creation",
            "type": "string"
        },
    ],
}


def test_renders_new():
    assert render_yaml(USER_CREATE_SCHEMA, [], []) == textwrap.dedent("""\
        # Object: user_create
        user_create:
          # Integer: Unix user ID
          # uid:

          # String: Username
          username:

          # Array: UNIX groups
          # groups:
            # Integer
            # -

          # Object: Additional attributes
          # attributes:

        # String: Force user creation
        # force: false
    """)


def test_renders_new_after_error():
    assert render_yaml(USER_CREATE_SCHEMA, [{"uid": 1000}], [
        Mock(attribute="user_create.uid", errmsg="User with such an UID already exists", errno=errno.EEXIST),
        Mock(attribute="user_create.invalid_field", errmsg="Unconsumed error", errno=errno.EEXIST),
    ]) == textwrap.dedent("""\
        # ERROR: Unconsumed error

        # Object: user_create
        user_create:
          # Integer: Unix user ID
          # ERROR: User with such an UID already exists
          uid: 1000

          # String: Username
          username:

          # Array: UNIX groups
          # groups:
            # Integer
            # -

          # Object: Additional attributes
          # attributes:

        # String: Force user creation
        # force: false
    """)


def test_renders_edit():
    assert render_yaml(USER_CREATE_SCHEMA, [{
        "uid": 1000,
        "username": "themylogin",
        "groups": [1, 2, 3],
        "attributes": {"extra_attribute": {"child": 0.5}},
    }, True], [
        Mock(attribute="user_create.groups.1", errmsg="You are not welcome here", errno=errno.EEXIST),
    ]) == textwrap.dedent("""\
        # Object: user_create
        user_create:
          # Integer: Unix user ID
          uid: 1000

          # String: Username
          username: themylogin

          # Array: UNIX groups
          groups:
            # Integer
            - 1
            # ERROR: You are not welcome here
            - 2
            - 3

          # Object: Additional attributes
          attributes:
            extra_attribute:
              child: 0.5

        # String: Force user creation
        force: true
    """)
