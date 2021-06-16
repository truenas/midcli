# -*- coding=utf-8 -*-
import logging

from .base import Editor
from .run import run_editor
from .utils import handle_yaml, YamlHandleError
from .yaml.render import render_yaml
from .yes_no import editor_yes_no_dialog

logger = logging.getLogger(__name__)

__all__ = ["InteractiveEditor"]


class InteractiveEditor(Editor):
    def edit(self, schema, values, errors):
        text = render_yaml(schema, values, errors)

        while True:
            text = run_editor(text)
            if not text.strip():
                print("Aborted")
                return None

            try:
                return handle_yaml(schema, text)
            except YamlHandleError as e:
                if editor_yes_no_dialog(e.title, e.text).run():
                    continue
                else:
                    print("Aborted")
                    return None

    def on_error(self, title, text):
        if editor_yes_no_dialog(title, text).run():
            return True
        else:
            print("Aborted.")
            return False
