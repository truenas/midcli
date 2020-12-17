# -*- coding=utf-8 -*-
import logging

logger = logging.getLogger(__name__)

__all__ = ["format_pyparsing_exception"]


def format_pyparsing_exception(e):
    foundstr = ""
    code = ""
    if e.pstr:
        if e.loc >= len(e.pstr):
            foundstr = ", found end of text"
        else:
            foundstr = (", found %r" % e.pstr[e.loc:e.loc + 1]).replace(r"\\", "\\")
            code = "\n " + e.pstr.split("\n")[e.lineno - 1].rstrip() + "\n" + " " * e.column + "^"

    return e.msg + foundstr + code
