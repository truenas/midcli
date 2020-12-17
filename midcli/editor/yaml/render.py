# -*- coding=utf-8 -*-
import logging

from .renderer import YamlRenderer

logger = logging.getLogger(__name__)

__all__ = ["render_yaml"]


def render_yaml(schema, values, errors):
    pre_rendered = YamlRenderer(schema, values, errors).render()
    return pre_rendered
