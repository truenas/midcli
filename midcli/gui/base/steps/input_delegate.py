# -*- coding=utf-8 -*-
import logging

from prompt_toolkit.styles import Style
from prompt_toolkit.validation import Validator, ValidationError

from midcli.utils.lang import undefined
from midcli.utils.prompt_toolkit.widgets.shortcuts import checkboxlist_dialog, input_dialog, radiolist_dialog

logger = logging.getLogger(__name__)

__all__ = ["create_input_delegate"]


def create_input_delegate(input, schema):
    if input.delegate:
        return input.delegate()

    type = schema["type"]
    nullable = False
    if isinstance(type, list) and len(type) == 2 and "null" in type:
        nullable = True
        type = [x for x in type if x != "null"][0]

    enum = input.enum or schema.get("enum")
    if enum:
        return EnumInputDelegate(enum, type == "array")

    if type == "boolean":
        return BooleanInputDelegate()

    if type == "integer":
        return IntegerInputDelegate(nullable)

    if type == "string":
        return StringInputDelegate()


class InputDelegate:
    def create_input_app(self, title, text, value):
        raise NotImplementedError

    def display_value(self, value):
        raise NotImplementedError

    def handle_value(self, value):
        return value


class BooleanInputDelegate(InputDelegate):
    def create_input_app(self, title, text, value):
        return radiolist_dialog(
            title=title,
            text=text,
            values=[(True, "Yes"), (False, "No")],
            style=Style.from_dict({
                "radio-selected": "bg:#aa0000 fg:white",
            }),
            current_value=value,
        )

    def display_value(self, value):
        return "Yes" if value else "No"


class EnumInputDelegate(InputDelegate):
    def __init__(self, enum, multiple):
        self.enum = enum
        self.multiple = multiple

    def create_input_app(self, title, text, value):
        kwargs = {}
        if self.multiple:
            factory = checkboxlist_dialog
            if value != undefined:
                kwargs["current_values"] = value
        else:
            factory = radiolist_dialog
            if value != undefined:
                kwargs["current_value"] = value

        return factory(
            title=title,
            text=text,
            values=[(v, v) for v in self.enum],
            style=Style.from_dict({
                "checkbox-selected": "bg:#aa0000 fg:white",
                "radio-selected": "bg:#aa0000 fg:white",
            }),
            **kwargs
        )

    def display_value(self, value):
        if self.multiple:
            if value:
                return ", ".join(value)
            else:
                return "<empty list>"
        else:
            return value


class IntegerInputDelegate(InputDelegate):
    def __init__(self, nullable):
        self.nullable = nullable

    def create_input_app(self, title, text, value):
        return input_dialog(
            title=title,
            text=text,
            validator=IntegerInputDelegateValidator(self.nullable),
            style=Style.from_dict({
                "dialog.body text-area": "#ffffff bg:#4444ff",
            }),
            value=str(value) if value not in [None, undefined] else "",
        )

    def display_value(self, value):
        if value is not None:
            return value
        else:
            return "<not set>"

    def handle_value(self, value):
        if self.nullable and not value:
            return None

        return int(value)


class IntegerInputDelegateValidator(Validator):
    def __init__(self, nullable):
        self.nullable = nullable

    def validate(self, document):
        text = document.text

        if text:
            try:
                int(text)
            except ValueError:
                raise ValidationError(message="This value should be an integer")
        else:
            if not self.nullable:
                raise ValidationError(message="This value is required")


class StringInputDelegate(InputDelegate):
    def create_input_app(self, title, text, value):
        return input_dialog(
            title=title,
            text=text,
            style=Style.from_dict({
                "dialog.body text-area": "#ffffff bg:#4444ff",
            }),
            value=value if value != undefined else "",
        )

    def display_value(self, value):
        if value:
            return value
        else:
            return "<empty string>"
