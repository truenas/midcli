# -*- coding=utf-8 -*-
import logging

logger = logging.getLogger(__name__)

__all__ = ["Command"]


class Command:
    builtin = False
    hidden = False
    name = None
    aliases = []
    description = None
    parent = None

    def __init__(self, context, namespace, name=None, description=None, args=None):
        self.context = context
        self.namespace = namespace
        if name:
            self.name = name
        if description:
            self.description = description
        if args:
            self.args = args

    def __lt__(self, other):
        return self.name < other.name

    def process_input(self, text):
        raise NotImplementedError

    def get_completions(self, text):
        raise NotImplementedError
