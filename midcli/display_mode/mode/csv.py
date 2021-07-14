# -*- coding=utf-8 -*-
import csv
import io
import logging

from midcli.utils.lang import undefined

from .base_table import TableDisplayModeBase

logger = logging.getLogger(__name__)

__all__ = ["CsvDisplayMode"]


class CsvDisplayMode(TableDisplayModeBase):
    def display_table(self, header, objects):
        file = io.StringIO()
        writer = csv.writer(file)
        writer.writerow(header)
        for object in objects:
            writer.writerow([
                self.value_to_text(object.get(k, undefined))
                for k in header
            ])
        return file.getvalue()

    def display_empty_list(self):
        return ""

    def display_empty_object(self):
        return ""

    def display_empty_header(self, count):
        return f"None of the specified fields found among {count} object(s)"
