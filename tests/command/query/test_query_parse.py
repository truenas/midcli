# -*- coding=utf-8 -*-
import pytest

from midcli.command.query.parse import ParsedQueryCommand, parse, ParseError


@pytest.mark.parametrize("text,result", [
    ("", ParsedQueryCommand([], {})),
    ("uid", ParsedQueryCommand([], {"select": ["uid"]})),
    ("uid,username", ParsedQueryCommand([], {"select": ["uid", "username"]})),
    ("uid,username WHERE uid > 0", ParsedQueryCommand([["uid", ">", 0]], {"select": ["uid", "username"]})),
    ("* WHERE uid > 0 and username != 'ivan'", ParsedQueryCommand(
        [["AND", [["uid", ">", 0], ["username", "!=", "ivan"]]]], {},
    )),
    ("* WHERE uid in [1, 2, 3]", ParsedQueryCommand(
        [["uid", "in", [1, 2, 3]]], {},
    )),
    ("* WHERE uid in (1, 2, 3)", ParsedQueryCommand(
        [["uid", "in", [1, 2, 3]]], {},
    )),
    ("* WHERE uid in {1, 2, 3}", ParsedQueryCommand(
        [["uid", "in", [1, 2, 3]]], {},
    )),
    ("* WHERE username.match('^i')", ParsedQueryCommand(
        [["username", "~", "^i"]], {},
    )),
    ("* WHERE username.startswith('i')", ParsedQueryCommand(
        [["username", "^", "i"]], {},
    )),
    ("* WHERE not username.startswith('i')", ParsedQueryCommand(
        [["NOT", ["username", "^", "i"]]], {},
    )),
    ("* WHERE username.endswith('i')", ParsedQueryCommand(
        [["username", "$", "i"]], {},
    )),
    ("* WHERE 'oo' in username", ParsedQueryCommand(
        [["username", "rin", "oo"]], {},
    )),
    ("* WHERE 'oo' not in username", ParsedQueryCommand(
        [["username", "rnin", "oo"]], {},
    )),
    ("* WHERE smb_account == null", ParsedQueryCommand(
        [["smb_account", "=", None]], {},
    )),
])
def test_parse(text, result):
    assert parse(text) == result


@pytest.mark.parametrize("text,error", [
    ("* WHERE uid &", ("invalid syntax\n"
                       " uid &\n"
                       "^")),
    ("* WHERE uid && 1", ("invalid syntax\n"
                          " uid && 1\n"
                          "      ^")),
    ("WHERE uid == 1", ("Expected end of text, found 'u'\n"
                        " WHERE uid == 1\n"
                        "       ^")),
    ("#test", ("Expected {column [, column]... | '*'}, found '#'\n"
               " #test\n"
               " ^")),
    ("* WHERE smb_account is not None", "Unsupported comparison operator: IsNot"),
    ("* WHERE 'oo' in 1", "Unsupported right operand for `oo in`"),
    ("* WHERE 1 > uid", "Unsupported left operand Constant"),
    ("* WHERE gid > uid", "Unsupported right operand Name"),
    ("* WHERE 'OO'.upper()", "Unsupported callee Constant"),
    ("* WHERE username.isdigit()", "Unknown function name 'isdigit'"),
    ("* WHERE username.match('ROOT', re.IGNORECASE)", "Function match accepts 1 argument, given 2"),
    ("* WHERE username.match('ROOT', flags=re.IGNORECASE)", "Function match does not accept keyword arguments"),
    ("* WHERE ~uid", "Unknown unary expression Invert"),
    ("* WHERE uid", "Unsupported filter expression: Name"),
])
def test_parse_error(text, error):
    with pytest.raises(ParseError) as e:
        parse(text)

    assert e.value.args[0] == error
