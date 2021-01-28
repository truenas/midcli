# -*- coding=utf-8 -*-
import textwrap

from midcli.editor.yaml.render import render_yaml

USER_CREATE_SCHEMA = {
    "accepts": [
        {
            "_attrs_order_": ["groups"],
            "_name_": "user_create",
            "properties": {
                "groups": {
                    "_name_": "groups",
                    "_required_": False,
                    "default": [],
                    "items": [],
                    "description": "UNIX groups",
                    "type": "array",
                },
            },
            "description": "user_create",
            "type": "object",
        },
    ],
}


def test_renders_new():
    assert render_yaml(USER_CREATE_SCHEMA, [], []) == textwrap.dedent("""\
        # Object: user_create
        user_create:
          # Array: UNIX groups
          # groups:

    """)
