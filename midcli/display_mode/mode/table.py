# -*- coding=utf-8 -*-
import io
import logging

import tableprint

from midcli.utils.lang import undefined

from .base_table import TableDisplayModeBase
from .text_mixin import TextMixin

logger = logging.getLogger(__name__)

__all__ = ["TableDisplayMode"]


class TableDisplayMode(TableDisplayModeBase, TextMixin):
    def display_object(self, object):
        if not object:
            return self.display_empty_object()

        table = [[k, self.value_to_text(v)] for k, v in object.items()]
        file = io.StringIO()
        tableprint.table(
            table,
            width=[max([len(r[0]) for r in table]), max([len(r[1]) for r in table])],
            out=file,
        )
        return file.getvalue()

    def display_table(self, header, objects):
        table = [
            [
                self.value_to_text(object.get(k, undefined))
                for k in header
            ]
            for object in objects
        ]
        file = io.StringIO()
        tableprint.table(
            table,
            headers=header,
            width=[max([len(h)] + [len(row[i]) for row in table]) for i, h in enumerate(header)],
            out=file,
        )
        return file.getvalue()

    def display_empty_list(self):
        return "(empty list)"

    def display_empty_object(self):
        return "(empty object)"

    def value_to_text(self, value):
        text = self._value_to_readable_text(value)

        if text is not undefined:
            if len(text) > 64:
                return f"{text[:61]}..."

            return text

        return f"<{type(value).__name__}>"
