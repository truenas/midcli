# -*- coding=utf-8 -*-
import json
import logging

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

        return json.dumps(value)
