# -*- coding=utf-8 -*-
import logging
import re

from prompt_toolkit.completion import Completion
import pyparsing

from .grammar import parse_query_command

logger = logging.getLogger(__name__)

__all__ = ["get_completions"]


def get_completions_for_prefix(options, prefix, exclude=None):
    exclude = exclude or []

    return [
        Completion(name, -len(prefix))
        for name in options
        if name.startswith(prefix) and name not in exclude
    ]


def get_completions(schema, text):
    if not schema:
        return []

    text_stripped = text.strip()

    if not text_stripped:
        return get_completions_for_prefix(schema["_attrs_order_"], "")

    try:
        parsed = parse_query_command(text, parseAll=False)
    except pyparsing.ParseException:
        return []

    if "where_clause" in parsed:
        where_clause = parsed["where_clause"]
        if not where_clause:
            return []

        prefix = None
        if not where_clause.strip():
            prefix = ""
        elif m := re.match(r"(.+\sand\s+|.+\sor\s+|.*\(|)\s*(?P<prefix>[a-z][a-z0-9_]*|)$", where_clause.lstrip(),
                           flags=re.IGNORECASE):
            prefix = m.group("prefix")

        if prefix is not None:
            return get_completions_for_prefix(schema["_attrs_order_"], prefix)
        else:
            return []
    elif "all_columns" in parsed:
        if text[-1].isspace():
            return [Completion("WHERE", 0)]
        else:
            return [Completion(" WHERE", 0)]
    else:
        columns = parsed["columns"].asList()

        if text_stripped[-1] == ",":
            return get_completions_for_prefix(schema["_attrs_order_"], "", columns)
        else:
            if text[-1].isspace():
                return [Completion("WHERE", 0)]

            return get_completions_for_prefix(
                [field for field in schema["_attrs_order_"] if field not in columns],
                columns[-1],
            )
