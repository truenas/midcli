# -*- coding=utf-8 -*-
import logging

from .polymorphic import PolymorphicDisplayMode
from .text_mixin import TextMixin

logger = logging.getLogger(__name__)

__all__ = ["TableDisplayModeBase"]


class TableDisplayModeBase(PolymorphicDisplayMode, TextMixin):
    def display_list(self, objects):
        if not objects:
            return self.display_empty_list()

        if not isinstance(objects[0], dict):
            return "\n".join([self.display_scalar(object) for object in objects])

        header = self._prepare_header(objects)
        if not header:
            return self.display_empty_header(len(objects))

        return self.display_table(header, objects)

    def display_object(self, object):
        if not object:
            return self.display_empty_object()

        return self.display_list([object])

    def display_scalar(self, scalar):
        return self.value_to_text(scalar)

    def display_table(self, header, objects):
        raise NotImplementedError

    def display_empty_list(self):
        raise NotImplementedError

    def display_empty_object(self):
        raise NotImplementedError

    def display_empty_header(self, count):
        raise NotImplementedError

    def _prepare_header(self, objects):
        header = []
        for object in objects:
            for prev, key in zip([None] + list(object.keys())[:-1], object.keys()):
                if key not in header:
                    if prev is None:
                        header.append(key)
                    else:
                        header.insert(header.index(prev) + 1, key)

        return header
