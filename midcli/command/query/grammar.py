# -*- coding=utf-8 -*-
import logging

import pyparsing as pp

logger = logging.getLogger(__name__)

__all__ = ["parse_query_command"]

column = pp.Word(pp.alphas, pp.alphanums + "_.").setName("column")
all_columns = pp.Literal("*")
select_expression = pp.delimitedList(column).setResultsName("columns") | all_columns.setResultsName("all_columns")

where_keyword = pp.Keyword("WHERE", caseless=True)
where_clause = where_keyword + pp.CharsNotIn("").setResultsName("where_clause")

command = select_expression + pp.Optional(where_clause)


def parse_query_command(text, parseAll=True):
    return dict(command.parseString(text, parseAll=parseAll).items())
