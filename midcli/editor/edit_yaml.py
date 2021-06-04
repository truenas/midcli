# -*- coding=utf-8 -*-
import logging

import yaml

from .run import run_editor
from .yaml.args import yaml_to_args, YamlToArgsError
from .yaml.render import render_yaml
from .yes_no import editor_yes_no_dialog

logger = logging.getLogger(__name__)

__all__ = ["edit_yaml"]


def edit_yaml(schema, values, errors):
    text = render_yaml(schema, values, errors)
    while True:
        text = run_editor(text)
        if not text.strip():
            return None

        try:
            doc = yaml.safe_load(text)
        except yaml.YAMLError as e:
            error_title = "YAML Syntax Error"
            error_text = str(e)
        else:
            try:
                args = yaml_to_args(schema, doc)
            except YamlToArgsError as e:
                error_title = "Semantic Error"
                error_text = str(e)
            else:
                return args

        if editor_yes_no_dialog(error_title, error_text).run():
            continue
        else:
            return None
