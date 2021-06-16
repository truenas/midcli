# -*- coding=utf-8 -*-
import logging

from .base import Editor
from .yaml.render import render_yaml

logger = logging.getLogger(__name__)

__all__ = ["PrintTemplateEditor"]


class PrintTemplateEditor(Editor):
    def edit(self, schema, values, errors):
        print(render_yaml(schema, values, errors))

    def on_error(self, title, text):
        assert False
