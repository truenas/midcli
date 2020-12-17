# -*- coding=utf-8 -*-
import logging

logger = logging.getLogger(__name__)

__all__ = ["DisplayMode"]


class DisplayMode:
    name = NotImplemented

    def display(self, value):
        raise NotImplementedError
