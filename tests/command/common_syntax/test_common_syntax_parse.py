# -*- coding=utf-8 -*-
import pytest

from midcli.command.common_syntax.parse import ParseError, parse_arguments


@pytest.mark.parametrize("s,result", [
    ("", ([], {})),
    ("1", ([1], {})),
    ("1a", "Expected end of text, found '1'\n"
           " 1a\n"
           " ^"),
    ("0o10", ([8], {})),
    ("0x10", ([16], {})),
    ("null", ([None], {})),
    ("[1, 2, 3]", ([[1, 2, 3]], {})),
    ("1 0o10", ([1, 8], {})),
    ("1 null", ([1, None], {})),
    ("1 [1, 2, 3]", ([1, [1, 2, 3]], {})),
    ("1 {\"key\": \"value\"} 2", ([1, {"key": "value"}, 2], {})),
    ("1 {\"key\": [\"nested\", {\"value\": 2}]} 3", ([1, {"key": ["nested", {"value": 2}]}, 3], {})),
    ("1 option=2", ([1], {"option": 2})),
    ("1 2 option=3", ([1, 2], {"option": 3})),
    ("1 2 option=3 another_option=\"4\"", ([1, 2], {"option": 3, "another_option": "4"})),
    ("1 option=2 3", "Expected end of text, found '3'\n"
                     " 1 option=2 3\n"
                     "            ^"),
    ("ivan_ivanov123", (["ivan_ivanov123"], {})),
    ("name=ivan_ivanov123", ([], {"name": "ivan_ivanov123"})),
    ("name= ivan_ivanov123", ([], {"name": "ivan_ivanov123"})),
    ("name =ivan_ivanov123", ([], {"name": "ivan_ivanov123"})),
    ("name = ivan_ivanov123", ([], {"name": "ivan_ivanov123"})),
])
def test__parse_arguments(s, result):
    if isinstance(result, str):
        with pytest.raises(ParseError) as e:
            print(parse_arguments(s))

        assert e.value.args[0] == result
    else:
        assert parse_arguments(s) == result
