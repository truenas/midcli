# -*- coding=utf-8 -*-
import logging
import sys

from .base import Editor
from .utils import handle_yaml, YamlHandleError

logger = logging.getLogger(__name__)

__all__ = ["NonInteractiveEditor"]


class NonInteractiveEditor(Editor):
    def __init__(self):
        if sys.stdin.isatty():
            self.available = False
            self.stdin = None
        else:
            self.available = True
            self.stdin = sys.stdin.read()

    def is_available(self):
        return self.available

    def edit(self, schema, values, errors):
        try:
            return handle_yaml(schema, self.stdin)
        except YamlHandleError as e:
            self.on_error(e.title, e.text)

    def on_error(self, title, text):
        print(title)
        print(text)
        sys.exit(1)
