# -*- coding=utf-8 -*-
import logging

from prettytable import PrettyTable

from midcli.utils.lang import undefined

from .base_table import TableDisplayModeBase
from .text_mixin import TextMixin

logger = logging.getLogger(__name__)

__all__ = ["TableDisplayMode"]


class TableDisplayMode(TableDisplayModeBase, TextMixin):
    def display_object(self, object):
        if not object:
            return self.display_empty_object()

        pt = PrettyTable()
        pt.add_column("key", list(object.keys()), "r")
        pt.add_column("value", list(map(self.value_to_text, object.values())), "l")
        return pt.get_string(header=False)

    def display_table(self, header, objects):
        table = [
            [
                self.value_to_text(object.get(k, undefined))
                for k in header
            ]
            for object in objects
        ]
        pt = PrettyTable()
        pt.field_names = header
        pt.align = "l"
        for row in table:
            pt.add_row(row)
        return pt.get_string()

    def display_empty_list(self):
        return "(empty list)"

    def display_empty_object(self):
        return "(empty object)"

    def display_empty_header(self, count):
        return f"(none of the specified fields found among {count} object(s))"

    def value_to_text(self, value):
        text = self._value_to_readable_text(value)

        if text is not undefined:
            lines = []
            for line in text.split("\n"):
                if len(line) > 64:
                    line = f"{line[:61]}..."
                lines.append(line)

            return "\n".join(lines)

        return f"<{type(value).__name__}>"
