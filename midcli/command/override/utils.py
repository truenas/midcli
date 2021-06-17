# -*- coding=utf-8 -*-
import functools
import logging

logger = logging.getLogger(__name__)

__all__ = ["rows_processor", "remove_fields"]


def rows_processor(f):
    @functools.wraps(f)
    def process_rows(context, result):
        if isinstance(result, dict):
            f(context, [result])
            return result

        if isinstance(result, list):
            f(context, result)

        return result

    return process_rows


def remove_fields(fields):
    if isinstance(fields, str):
        fields = [fields]

    return rows_processor(functools.partial(_remove_fields, fields))


def _remove_fields(fields, context, result):
    for row in result:
        for field in fields:
            row.pop(field, None)
