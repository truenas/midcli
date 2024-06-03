# -*- coding=utf-8 -*-
from datetime import date, datetime, time
import logging

from truenas_api_client import ejson

from midcli.utils.lang import undefined

logger = logging.getLogger(__name__)

__all__ = ["TextMixin"]


class TextMixin:
    def value_to_text(self, value):
        text = self._value_to_readable_text(value)

        if text is not undefined:
            return text

        return ejson.dumps(value)

    def _value_to_readable_text(self, value):
        if value is undefined:
            return "<undefined>"

        if value is None:
            return "<null>"

        if isinstance(value, (bool, int, float)):
            return ejson.dumps(value)

        if isinstance(value, str):
            return value

        if isinstance(value, (date, datetime, time)):
            return value.isoformat()

        if isinstance(value, list):
            if not value:
                return "<empty list>"

            readable_texts = list(map(self._value_to_readable_text, value))
            if all(rt != undefined for rt in readable_texts):
                return "\n".join(readable_texts)

        return undefined
