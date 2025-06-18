# -*- coding=utf-8 -*-
import logging
import typing

from prompt_toolkit.shortcuts import message_dialog
from prompt_toolkit.styles import Style
from prompt_toolkit.validation import Validator, ValidationError

from midcli.utils.lang import undefined
from midcli.utils.prompt_toolkit.widgets.shortcuts import checkboxlist_dialog, input_dialog, radiolist_dialog
if typing.TYPE_CHECKING:
    from midcli.gui.base.steps.input import Input

logger = logging.getLogger(__name__)

__all__ = ["create_input_delegate"]


def create_input_delegate(input: "Input", schema: dict) -> "InputDelegate":
    if input.delegate:
        return input.delegate()

    if "type" in schema:
        type = schema["type"]
    elif "enum" in schema:
        type = set()
        for v in schema["enum"]:
            if v is None:
                type.add("null")
            elif isinstance(v, str):
                type.add("string")
    elif "anyOf" in schema and (type := {s["type"] for s in schema["anyOf"]}):
        pass
    else:
        raise ValueError(f"Unable to create input delegate for schema {schema!r}")

    nullable = False
    if isinstance(type, set):
        if len(type) == 1:
            type = type.pop()
        elif len(type) == 2 and "null" in type:
            nullable = True
            type = next(filter(lambda x: x != "null", type))

    if input.enum is undefined:
        enum = schema.get("enum")
    else:
        enum = input.enum

    if enum is not None:
        return EnumInputDelegate(enum, type == "array")

    if type == "boolean":
        return BooleanInputDelegate()

    if type == "integer":
        return IntegerInputDelegate(nullable)

    if type == "string":
        return StringInputDelegate()

    raise ValueError(f"Unable to create input delegate for schema {schema!r}")


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
        if not self.enum:
            return message_dialog(title, "No items available for selection.")

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
