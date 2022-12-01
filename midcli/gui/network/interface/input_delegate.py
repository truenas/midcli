# -*- coding=utf-8 -*-
import functools
import logging

from prompt_toolkit.styles import Style
from prompt_toolkit.validation import Validator, ValidationError

from midcli.gui.base.steps.input_delegate import InputDelegate
from midcli.utils.lang import undefined
from midcli.utils.prompt_toolkit.widgets.shortcuts import input_dialog
from midcli.utils.truenas.interface import alias_to_str, str_to_alias

logger = logging.getLogger(__name__)

__all__ = ["AliasesInputDelegate"]


def split(value):
    return value.replace(",", " ").split()


class AliasesInputDelegate(InputDelegate):
    def __init__(self, netmask=True):
        self.netmask = netmask
        self.alias_to_str = functools.partial(alias_to_str, netmask=netmask)
        self.str_to_alias = functools.partial(str_to_alias, netmask=netmask)

    def create_input_app(self, title, text, value):
        return input_dialog(
            title,
            " ".join(map(self.alias_to_str, value)) if value != undefined else "",
            validator=AliasesInputDelegateValidator(self.netmask),
            style=Style.from_dict({
                "dialog.body text-area": "#ffffff bg:#4444ff",
            }),
        )

    def display_value(self, value):
        if value:
            return " ".join(map(self.alias_to_str, value))
        else:
            return "<empty list>"

    def handle_value(self, value):
        return list(map(self.str_to_alias, split(value)))


class AliasesInputDelegateValidator(Validator):
    def __init__(self, netmask=True):
        self.str_to_alias = functools.partial(str_to_alias, netmask=netmask)

    def validate(self, document):
        text = document.text

        if text:
            for v in split(text):
                try:
                    self.str_to_alias(v)
                except ValueError as e:
                    raise ValidationError(message=str(e))
