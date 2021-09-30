# -*- coding=utf-8 -*-
import pytest

from midcli.command.common_syntax.parse import AutocompleteName, AutocompleteValue, get_autocomplete


@pytest.mark.parametrize("s,result", [
    ("", AutocompleteName(0, [], "")),
    ("us", AutocompleteName(0, [], "us")),
    ("us ", AutocompleteName(1, [], "")),
    ("username p", AutocompleteName(1, [], "p")),
    ("username password=", AutocompleteValue("password", "")),
    ("username password =", AutocompleteValue("password", "")),
    ("username password = ", AutocompleteValue("password", "")),
    ("username password=i", AutocompleteValue("password", "i")),
    ("username password = i", AutocompleteValue("password", "i")),
    ("username password=\"i", AutocompleteValue("password", "\"i")),
    ("username password=\"i ", AutocompleteValue("password", "\"i ")),
    ("username password=\"i v\" ", AutocompleteName(1, ["password"], "")),
    ("username password=\"i v\" ke", AutocompleteName(1, ["password"], "ke")),
    ("username password=\"i v\" key=", AutocompleteValue("key", "")),
    ("6", AutocompleteName(0, [], "6")),
    ("id=6", AutocompleteValue("id", "6")),
])
def test__get_autocomplete(s, result):
    assert get_autocomplete(s) == result
