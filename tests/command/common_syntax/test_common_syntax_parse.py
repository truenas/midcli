# -*- coding=utf-8 -*-
import pytest

from midcli.command.common_syntax.parse import ParseError, CommonSyntaxCommandArguments, parse_arguments


@pytest.mark.parametrize("s,result", [
    ("", CommonSyntaxCommandArguments([], {})),
    ("1", CommonSyntaxCommandArguments([1], {})),
    ("1a", "Expected end of text, found '1'\n"
           " 1a\n"
           " ^"),
    ("0o10", CommonSyntaxCommandArguments([8], {})),
    ("0x10", CommonSyntaxCommandArguments([16], {})),
    ("null", CommonSyntaxCommandArguments([None], {})),
    ("[1, 2, 3]", CommonSyntaxCommandArguments([[1, 2, 3]], {})),
    ("1 0o10", CommonSyntaxCommandArguments([1, 8], {})),
    ("1 null", CommonSyntaxCommandArguments([1, None], {})),
    ("1 [1, 2, 3]", CommonSyntaxCommandArguments([1, [1, 2, 3]], {})),
    ("1 1,2,3", CommonSyntaxCommandArguments([1, [1, 2, 3]], {})),
    ("1 1,2, 3", CommonSyntaxCommandArguments([1, [1, 2, 3]], {})),
    ("1 \"a,b\",\"c, d\"", CommonSyntaxCommandArguments([1, ["a,b", "c, d"]], {})),
    ("1 {\"key\": \"value\"} 2", CommonSyntaxCommandArguments([1, {"key": "value"}, 2], {})),
    ("1 {\"key\": [\"nested\", {\"value\": 2}]} 3", CommonSyntaxCommandArguments([1, {"key": ["nested", {"value": 2}]}, 3], {})),
    ("1 option=2", CommonSyntaxCommandArguments([1], {"option": 2})),
    ("1 2 option=3", CommonSyntaxCommandArguments([1, 2], {"option": 3})),
    ("1 2 option=3,4", CommonSyntaxCommandArguments([1, 2], {"option": [3, 4]})),
    ("1 2 option=3 another_option=\"4\"", CommonSyntaxCommandArguments([1, 2], {"option": 3, "another_option": "4"})),
    ("1 option=2 3", "Expected end of text, found '3'\n"
                     " 1 option=2 3\n"
                     "            ^"),
    ("ivan_ivanov123", CommonSyntaxCommandArguments(["ivan_ivanov123"], {})),
    ("name=ivan_ivanov123", CommonSyntaxCommandArguments([], {"name": "ivan_ivanov123"})),
    ("name= ivan_ivanov123", CommonSyntaxCommandArguments([], {"name": "ivan_ivanov123"})),
    ("name =ivan_ivanov123", CommonSyntaxCommandArguments([], {"name": "ivan_ivanov123"})),
    ("name = ivan_ivanov123", CommonSyntaxCommandArguments([], {"name": "ivan_ivanov123"})),
    ("path=/", CommonSyntaxCommandArguments([], {"path": "/"})),
    ("path=.history", CommonSyntaxCommandArguments([], {"path": ".history"})),
    ("user=root@localhost", CommonSyntaxCommandArguments([], {"user": "root@localhost"})),
    ("--", CommonSyntaxCommandArguments([], {}, True)),
    ("1 --", CommonSyntaxCommandArguments([1], {}, True)),
    ("1 option=2 --", CommonSyntaxCommandArguments([1], {"option": 2}, True)),
    ("1 option=2\t-- ", CommonSyntaxCommandArguments([1], {"option": 2}, True)),
    ("1 option=2 > file.tar.gz", CommonSyntaxCommandArguments([1], {"option": 2}, False, "file.tar.gz")),
    ("1 option=2 -- > /root/file.tar.gz", CommonSyntaxCommandArguments([1], {"option": 2}, True, "/root/file.tar.gz")),
    ("auxsmbconf=\"force group=apps\\nforce user=apps\"", CommonSyntaxCommandArguments([], {
        "auxsmbconf": "force group=apps\nforce user=apps",
    })),
])
def test__parse_arguments(s, result):
    if isinstance(result, str):
        with pytest.raises(ParseError) as e:
            print(parse_arguments(s))

        assert e.value.args[0] == result
    else:
        assert parse_arguments(s) == result
