# -*- coding=utf-8 -*-
import pytest

from midcli.editor.yaml.object import object_to_yaml_arg


@pytest.mark.parametrize("schema,object,yaml_arg", [
    (
        {
            "properties": {
                "group": {
                    "type": "integer",
                    "_name_": "group",
                    "title": "group",
                    "_required_": False,
                },
            },
        },
        {
            "group": {
                "id": 41,
                "bsdgrp_gid": 0,
                "bsdgrp_group": "root",
                "bsdgrp_builtin": True,
                "bsdgrp_sudo": False,
                "bsdgrp_smb": False,
            },
        },
        {
            "group": 41,
        }
    )
])
def test__object_to_yaml_arg(schema, object, yaml_arg):
    assert object_to_yaml_arg(schema, object) == yaml_arg
