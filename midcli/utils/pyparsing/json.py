# jsonParser.py
#
# Implementation of a simple JSON parser, returning a hierarchical
# ParseResults object support both list- and dict-style data access.
#
# Copyright 2006, by Paul McGuire
#
# Updated 8 Jan 2007 - fixed dict grouping bug, and made elements and
#   members optional in array and object collections
#
# Updated 9 Aug 2016 - use more current pyparsing constructs/idioms
#
import json

import pyparsing as pp
from pyparsing import pyparsing_common as ppc

json_bnf = """
object
    { members }
    {}
members
    string : value
    members , string : value
array
    [ elements ]
    []
elements
    value
    elements , value
value
    string
    number
    object
    array
    true
    false
    null
"""


def make_keyword(kwd_str, kwd_value):
    return pp.Keyword(kwd_str).setParseAction(pp.replaceWith(kwd_value))


TRUE = make_keyword("true", True)
FALSE = make_keyword("false", False)
NULL = make_keyword("null", None)

LBRACK, RBRACK, LBRACE, RBRACE, COLON = map(pp.Suppress, "[]{}:")

jsonString = pp.dblQuotedString().setParseAction(lambda _, __, t: json.loads(t[0]))
jsonNumber = ppc.number()

jsonObject = pp.Forward().setName("jsonObject")
jsonValue = pp.Forward().setName("jsonValue")

jsonElements = pp.delimitedList(jsonValue)

jsonArray = pp.Group(
    LBRACK + pp.Optional(jsonElements) + RBRACK, aslist=True
)

jsonValue << (jsonString | jsonNumber | jsonObject | jsonArray | TRUE | FALSE | NULL)

memberDef = pp.Group(
    jsonString + COLON + jsonValue, aslist=True
).setName("jsonMember")

jsonMembers = pp.delimitedList(memberDef)
jsonObject << pp.Dict(
    LBRACE + pp.Optional(jsonMembers) + RBRACE, asdict=True
)

jsonComment = pp.cppStyleComment
jsonObject.ignore(jsonComment)
