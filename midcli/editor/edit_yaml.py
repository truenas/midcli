# -*- coding=utf-8 -*-
import logging

from prompt_toolkit.shortcuts import yes_no_dialog
import yaml

from .run import run_editor
from .yaml.args import yaml_to_args, YamlToArgsError
from .yaml.render import render_yaml

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
            error_text = f"The input you provided has invalid YAML syntax:\n\n{str(e)}"
        else:
            try:
                args = yaml_to_args(schema, doc)
            except YamlToArgsError as e:
                error_title = "Semantic Error"
                error_text = str(e)
            else:
                return args

        if yes_no_dialog(
            title=error_title,
            text=error_text + "\n\nContinue?",
        ).run():
            continue
        else:
            return None
