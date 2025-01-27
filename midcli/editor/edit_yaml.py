# -*- coding=utf-8 -*-
import logging

from prompt_toolkit.application import get_app
import yaml

from .run import run_editor
from .yaml.args import yaml_to_args, YamlToArgsError
from .yaml.render import render_yaml
from .yes_no import editor_yes_no_dialog

logger = logging.getLogger(__name__)

__all__ = ["edit_yaml"]


def edit_yaml(schema, values, errors, input=None, output=False):
    """
    Offer user to edit YAML arguments for method call defined by `schema`.
    `values` will be inserted instead of defaults and `errors` will be displayed in the comments section.

    If `input` is not `None` then editor won't be ran and its value would be used instead of user's
    input.
    If `output` is `True` then editor won't be ran and YAML template would be printed to stdout.
    In both cases program will be terminated.
    """
    text = render_yaml(schema, values, errors)
    if output:
        print(text)
        get_app().exit()

    while True:
        if input is not None:
            text = input
        else:
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

        if input is not None:
            print(f"{error_title}: {error_text}")
            get_app().exit()

        if editor_yes_no_dialog(error_title, error_text).run():
            continue
        else:
            return None
