# -*- coding=utf-8 -*-
from datetime import date, datetime, time
import logging

from middlewared.client import ejson

from midcli.utils.lang import undefined

logger = logging.getLogger(__name__)

__all__ = ["TextMixin"]


class TextMixin:
    def value_to_text(self, value):
        if value is undefined:
            return "<undefined>"

        if value is None:
            return "<null>"

        if isinstance(value, str):
            return value

        if isinstance(value, (date, datetime, time)):
            return value.isoformat()

        return ejson.dumps(value)
