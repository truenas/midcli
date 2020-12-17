# -*- coding=utf-8 -*-
import ast
from collections import namedtuple
import logging

import pyparsing

from midcli.utils.pyparsing.exception import format_pyparsing_exception

from .grammar import parse_query_command

logger = logging.getLogger(__name__)

__all__ = ["parse", "ParseError"]

ParsedQueryCommand = namedtuple("QueryCommand", ["filters", "options"])


class ParseError(Exception):
    pass


def parse(text):
    filters = []
    options = {}

    if text.strip():
        try:
            parsed = parse_query_command(text)
        except pyparsing.ParseException as e:
            raise ParseError(format_pyparsing_exception(e))

        if "where_clause" in parsed and parsed["where_clause"].strip():
            filters = [parse_filters(parsed["where_clause"].strip())]

        if "all_columns" not in parsed:
            options["select"] = parsed["columns"].asList()

    return ParsedQueryCommand(filters, options)


def parse_filters(text):
    try:
        expression = ast.parse(text, mode="eval")
    except SyntaxError as e:
        raise ParseError(f"{e.msg}\n {e.text}\n{' ' * e.offset}^")

    return parse_filter(expression.body)


def parse_filter(op):
    if isinstance(op, ast.BoolOp):
        filter_op = {
            ast.And: "AND",
            ast.Or: "OR",
        }.get(op.op.__class__)
        if filter_op is None:
            raise ParseError(f"Unsupported boolean operator {op.op!r}")

        return [filter_op, [parse_filter(v) for v in op.values]]

    if isinstance(op, ast.Compare):
        if len(op.comparators) != 1:
            raise ParseError(f"Too many comparators (expected 1, found {len(op.comparators)}")

        comparator = op.comparators[0]

        filter_op = {
            ast.Eq: "=",
            ast.NotEq: "!=",
            ast.Gt: ">",
            ast.GtE: ">=",
            ast.Lt: "<",
            ast.LtE: "<=",
            ast.In: "in",
            ast.NotIn: "nin",
        }.get(op.ops[0].__class__)
        if filter_op is None:
            raise ParseError(f"Unsupported comparison operator: {op.ops[0].__class__.__name__}")

        if filter_op in ["in", "nin"] and isinstance(op.left, ast.Constant):
            if not isinstance(comparator, ast.Name):
                raise ParseError(f"Unsupported right operand for `{op.left.value} {filter_op}`")

            return [comparator.id, f"r{filter_op}", op.left.value]

        if not isinstance(op.left, ast.Name):
            raise ParseError(f"Unsupported left operand {op.left.__class__.__name__}")

        return [op.left.id, filter_op, handle_filter_constant(comparator)]

    if isinstance(op, ast.Call):
        if not isinstance(op.func, ast.Attribute):
            raise ParseError(f"Unsupported callee type: {op.func!r}")

        if not isinstance(op.func.value, ast.Name):
            raise ParseError(f"Unsupported callee {op.func.value.__class__.__name__}")

        filter_op = {
            "match": "~",
            "startswith": "^",
            "endswith": "$",
        }.get(op.func.attr)
        if filter_op is None:
            raise ParseError(f"Unknown function name {op.func.attr!r}")

        if len(op.args) != 1:
            raise ParseError(f"Function {op.func.attr} accepts 1 argument, given {len(op.args)}")
        if op.keywords:
            raise ParseError(f"Function {op.func.attr} does not accept keyword arguments")

        left = op.func.value.id
        right = handle_filter_constant(op.args[0])
        return [left, filter_op, right]

    if isinstance(op, ast.UnaryOp):
        if isinstance(op.op, ast.Not):
            return ["NOT", parse_filter(op.operand)]

        raise ParseError(f"Unknown unary expression {op.op.__class__.__name__}")

    raise ParseError(f"Unsupported filter expression: {op.__class__.__name__}")


def handle_filter_constant(op):
    if isinstance(op, ast.Constant):
        return op.value

    if isinstance(op, (ast.List, ast.Set, ast.Tuple)):
        return [handle_filter_constant(el) for el in op.elts]

    if isinstance(op, ast.Name):
        mapping = {
            "false": False,
            "true": True,
            "null": None,
        }
        if op.id in mapping:
            return mapping[op.id]

    raise ParseError(f"Unsupported right operand {op.__class__.__name__}")
