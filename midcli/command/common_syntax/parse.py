# -*- coding=utf-8 -*-
from collections import namedtuple
from dataclasses import dataclass
import functools
import logging
import re
import typing

import pyparsing as pp

from midcli.utils.pyparsing.exception import format_pyparsing_exception
from midcli.utils.pyparsing.json import jsonValue

logger = logging.getLogger(__name__)

__all__ = ["AutocompleteName", "AutocompleteValue", "ParseError", "RE_SIMPLE_STRING", "CommonSyntaxCommandArguments",
           "parse_arguments", "get_autocomplete"]


AutocompleteName = namedtuple("AutocompleteName", ["args", "kwargs", "name"])
AutocompleteValue = namedtuple("AutocompleteValue", ["name", "value"])


class ParseError(Exception):
    pass


name = pp.Word(pp.alphas, pp.alphanums + "_").setName("name")

oct = pp.Regex(r"0o[0-7]+", flags=re.IGNORECASE).setName("oct").setParseAction(lambda toks: int(toks[0][2:], 8))
hex = pp.Regex(r"0x[0-9a-f]+", flags=re.IGNORECASE).setName("hex").setParseAction(lambda toks: int(toks[0][2:], 16))
string = pp.Regex(r"[a-z./_@][a-z0-9./_@]*", flags=re.IGNORECASE).setName("string").setParseAction(lambda toks: toks[0])
RE_SIMPLE_STRING = re.compile(r"[a-z\\./_@][a-z0-9\\./_@]*$", flags=re.IGNORECASE)
json = jsonValue.setName("json")

baseValue = (oct | hex | json | string).setName("baseValue")
baseValueList = (
    (baseValue + pp.OneOrMore((pp.Suppress(",") + baseValue).leaveWhitespace())).
    leaveWhitespace().
    setName("baseValueList")
)

value = (baseValueList | baseValue).setName("value")

arg = value.setResultsName("arg_value", listAllMatches=True) + ~pp.FollowedBy("=")
kwarg = (
    name.setResultsName("kwarg_name", listAllMatches=True) +
    pp.Literal("=") +
    value.setResultsName("kwarg_value", listAllMatches=True)
).setName("kwarg")

arguments = (
    pp.ZeroOrMore(arg + pp.FollowedBy(pp.White())).setName("args") +
    pp.ZeroOrMore(kwarg + pp.FollowedBy(pp.White())).setName("kwargs")
)

command = (
    arguments +
    pp.Optional(pp.Literal("--")).setResultsName("interactive") +
    pp.Optional(pp.Literal(">") + pp.Word(pp.printables).setResultsName("output"))
)

autocomplete = arguments + pp.restOfLine.setResultsName("rest")

RE_ARG = re.compile(r"\s*(?P<name>[a-z0-9_]+)$", flags=re.IGNORECASE)
RE_KWARG = re.compile(r"\s*(?P<name>[a-z0-9_]+)\s*=\s*(?P<value>.*)$", flags=re.IGNORECASE)


@dataclass
class CommonSyntaxCommandArguments:
    args: []
    kwargs: {}
    interactive: bool = False
    output: typing.Optional[str] = None


def parse_arguments(text):
    args = []
    kwargs = {}
    interactive = False
    output = None

    if text is not None:
        try:
            result = dict(command.parseString(text + " ", parseAll=True).items())
        except pp.ParseException as e:
            raise ParseError(format_pyparsing_exception(e))

        if "arg_value" in result:
            args = list(map(get_value, result["arg_value"]))

        if "kwarg_name" in result:
            kwargs = dict(zip(result["kwarg_name"], map(get_value, result["kwarg_value"])))

        if "interactive" in result:
            interactive = True

        if "output" in result:
            output = result["output"]

    return CommonSyntaxCommandArguments(args, kwargs, interactive, output)


def get_value(value):
    if len(value) == 1:
        # baseValue
        return value[0]
    else:
        # baseValueList
        return list(value)


def get_autocomplete(text):
    try:
        result = dict(autocomplete.parseString(text + " ", parseAll=True).items())
    except pp.ParseException:
        return None

    result["rest"] = result["rest"][:-1]
    if not result["rest"]:
        del result["rest"]

    if "arg_value" in result:
        result["arg_value"] = list(map(get_value, result["arg_value"]))

    if "kwarg_value" in result:
        result["kwarg_value"] = list(map(get_value, result["kwarg_value"]))

    args = len(result.get("arg_value", []))
    kwargs = list(result.get("kwarg_name", []))
    autocomplete_name = functools.partial(AutocompleteName, args, kwargs)

    if not result:
        return autocomplete_name("")

    if set(result.keys()) == {"arg_value"}:
        if text.endswith(" "):
            return autocomplete_name("")
        else:
            return AutocompleteName(args - 1, kwargs, str(result["arg_value"][-1]))

    if "rest" not in result:
        return AutocompleteValue(result["kwarg_name"][-1], str(result["kwarg_value"][-1]))

    if m := RE_ARG.match(result["rest"]):
        return autocomplete_name(m.group("name"))
    if m := RE_KWARG.match(result["rest"]):
        return AutocompleteValue(m.group("name"), m.group("value"))
    else:
        return autocomplete_name("")
