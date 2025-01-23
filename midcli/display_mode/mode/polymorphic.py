# -*- coding=utf-8 -*-
import logging

from .interface import DisplayMode

logger = logging.getLogger(__name__)

__all__ = ["PolymorphicDisplayMode"]


class PolymorphicDisplayMode(DisplayMode):
    def display(self, value):
        if isinstance(value, list):
            return self.display_list(value)

        if isinstance(value, dict):
            return self.display_object(value)

        return self.display_scalar(value)

    def display_list(self, objects):
        raise NotImplementedError

    def display_object(self, object):
        raise NotImplementedError

    def display_scalar(self, scalar):
        raise NotImplementedError
