# -*- coding=utf-8 -*-
import textwrap

import pytest
import yaml

from midcli.editor.yaml.args import yaml_to_args, YamlToArgsError


@pytest.mark.parametrize("names,doc,result", [
    (
        ["user_create", "force"],
        textwrap.dedent("""\
            user_create:
              uid: 1
            force: true
        """),
        [{"uid": 1}, True],
    ),
    (
        ["user_create", "force"],
        textwrap.dedent("""\
            user_create:
              uid: 1
            # force: false
        """),
        [{"uid": 1}],
    ),
    (
        ["user_create", "force", "horse"],
        textwrap.dedent("""\
            user_create:
              uid: 1
            # force: false
            horse: 123
        """),
        "Element #2 should be 'force', 'horse' given",
    ),
])
def test_yaml_to_args(names, doc, result):
    schema = {"accepts": [{"_name_": name} for name in names]}
    doc = yaml.safe_load(doc)
    if isinstance(result, list):
        assert yaml_to_args(schema, doc) == result
    else:
        with pytest.raises(YamlToArgsError) as e:
            yaml_to_args(schema, doc)

        assert e.value.args[0] == result


def test_yaml_to_args_null_object():
    schema = {"accepts": [{"_name_": "options", "type": "object"}]}
    assert yaml_to_args(schema, {"options": None}) == [{}]
