# -*- coding=utf-8 -*-
import logging

import yaml

from .yaml.args import yaml_to_args, YamlToArgsError

logger = logging.getLogger(__name__)

__all__ = ["handle_yaml", "YamlHandleError"]


def handle_yaml(schema, text):
    try:
        doc = yaml.safe_load(text)
    except yaml.YAMLError as e:
        raise YamlHandleError("YAML Syntax Error", str(e))
    else:
        try:
            args = yaml_to_args(schema, doc)
        except YamlToArgsError as e:
            raise YamlHandleError("Semantic Error", str(e))
        else:
            return args


class YamlHandleError(Exception):
    def __init__(self, title, text):
        self.title = title
        self.text = text
        super().__init__(self.title, self.text)
