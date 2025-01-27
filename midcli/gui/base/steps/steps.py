# -*- coding=utf-8 -*-
import enum
import itertools
import logging

from prompt_toolkit.filters import has_focus
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.key_binding.bindings.focus import focus_next, focus_previous
from prompt_toolkit.key_binding.key_bindings import KeyBindings
from prompt_toolkit.layout.containers import (
    AnyContainer,
    HSplit,
    VSplit,
)
from prompt_toolkit.layout.dimension import Dimension as D
from prompt_toolkit.shortcuts.dialogs import _create_app
from prompt_toolkit.widgets import Label
from prompt_toolkit.widgets.base import Box, Button, Frame, Shadow

from truenas_api_client import ClientException, ValidationErrors

from midcli.gui.base.app import AppResult
from midcli.gui.base.common.menu_item import MenuItem
from midcli.middleware import format_error, format_validation_errors
from midcli.utils.lang import undefined

from .error import Error
from .header import Header
from .input import Input
from .input_delegate import create_input_delegate

logger = logging.getLogger(__name__)

__all__ = ["Steps", "StepsMethod"]


class StepsMethod(enum.Enum):
    CONFIG = "config"
    CREATE = "create"
    UPDATE = "update"


class Steps:
    title = NotImplemented

    service = NotImplemented

    method = NotImplemented
    primary_key = "id"

    def __init__(self, context, back_app=None, data=None, errors=None, active_input=None):
        self.context = context
        self.back_app = back_app
        self.data = data or {}
        self.errors = errors or {}

        if self.method == StepsMethod.CONFIG:
            self.schema = context.methods[f"{self.service}.update"]["accepts"][0]["properties"]
            if not self.data:
                with self.context.get_client() as c:
                    self.data = c.call(f"{self.service}.config")
        else:
            self.schema = context.methods[f"{self.service}.create"]["accepts"][0]["properties"]

        widgets, self.focus, complete = self._draw(active_input)
        inputs = list(filter(lambda w: not isinstance(w, Label), widgets))

        buttons = []
        if complete:
            buttons.append(Button(text="Save", handler=self._save, width=6))
        buttons.append(Button(text="Back", handler=self._back, width=6))

        inputs_kb = KeyBindings()
        first_input_selected = has_focus(inputs[0])
        last_input_selected = has_focus(inputs[-1])
        inputs_kb.add("up", filter=first_input_selected)(lambda event: event.app.layout.focus(buttons[-1]))
        inputs_kb.add("up", filter=~first_input_selected)(focus_previous)
        inputs_kb.add("down", filter=last_input_selected)(lambda event: event.app.layout.focus(buttons[0]))
        inputs_kb.add("down", filter=~last_input_selected)(focus_next)

        buttons_kb = KeyBindings()
        first_button_selected = has_focus(buttons[0])
        last_button_selected = has_focus(buttons[-1])
        buttons_kb.add("up", filter=first_button_selected)(lambda event: event.app.layout.focus(inputs[-1]))
        buttons_kb.add("up", filter=~first_button_selected)(focus_previous)
        buttons_kb.add("down", filter=last_button_selected)(lambda event: event.app.layout.focus(inputs[0]))
        buttons_kb.add("down", filter=~last_button_selected)(focus_next)
        buttons_kb.add("left", filter=first_button_selected)(lambda event: event.app.layout.focus(buttons[-1]))
        buttons_kb.add("left", filter=~first_button_selected)(focus_previous)
        buttons_kb.add("right", filter=last_button_selected)(lambda event: event.app.layout.focus(buttons[0]))
        buttons_kb.add("right", filter=~last_button_selected)(focus_next)

        frame_body = HSplit(
            [
                Box(
                    body=HSplit(widgets, padding=0, key_bindings=inputs_kb),
                ),
                Box(
                    body=VSplit(buttons, padding=1, key_bindings=buttons_kb),
                    height=D(min=1, max=3, preferred=3),
                ),
            ]
        )

        frame = Shadow(
            body=Frame(
                title=lambda: self.title,
                body=frame_body,
                style="class:dialog.body",
                width=None,
                modal=True,
            )
        )

        self.container = Box(body=frame, style="class:dialog", width=None)

        self.app = None

    def __pt_container__(self) -> AnyContainer:
        return self.container

    def run(self):
        self.app = _create_app(self, None)

        if self.focus:
            self.app.layout.focus(self.focus)

        return self.app.run()

    def _with_data(self, data, active_input):
        return self.__class__(self.context, self.back_app, data, active_input=active_input)

    def _with_errors(self, errors):
        return self.__class__(self.context, self.back_app, self.data, errors=errors)

    def _draw(self, active_input):
        widgets = []
        complete = False

        if None in self.errors:
            widgets.append(Error(self.errors[None]))

        for step in itertools.count(1):
            meth = getattr(self, f"step{step}", None)
            if meth is None:
                complete = True
                break

            step_widgets = meth(self.data)
            self._extend_widgets(step_widgets)

            widgets.extend(step_widgets)

            step_inputs = list(filter(lambda w: isinstance(w, Input), step_widgets))
            if not all(self._input_complete(input) for input in step_inputs):
                break

        focus = None
        if active_input:
            for i, widget in enumerate(widgets):
                if isinstance(widget, Input):
                    if widget.name == active_input.name:
                        focus = i
                        break

        apps = self._draw_widgets(widgets)
        return apps, apps[focus] if focus is not None else None, complete

    def _extend_widgets(self, widgets):
        for input in filter(lambda w: isinstance(w, Input), widgets):
            schema = self.schema[input.name]

            if input.default == undefined:
                if "default" in schema:
                    input.default = schema["default"]

            if input.empty == undefined:
                if "empty" in schema:
                    input.empty = schema["empty"]

            if input.required == undefined:
                input.required = schema["_required_"]

    def _input_complete(self, input: Input):
        return input_complete(input, self.data)

    def _draw_widgets(self, widgets: [Error, Header, Input]):
        label_length = max(map(len, [self.schema[widget.name]["title"]
                                     for widget in widgets
                                     if isinstance(widget, Input)]))

        return [
            self._draw_widget(widget, label_length)
            for widget in widgets
        ]

    def _draw_widget(self, widget: [Error, Header, Input], label_length):
        if isinstance(widget, Error):
            return Label(FormattedText([
                ("bg:red fg:white", "Error:"),
                ("", f" {widget.title}\n"),
            ]))

        if isinstance(widget, Header):
            return Label(widget.title, style="bg:black fg:white")

        return self._draw_input(widget, label_length)

    def _draw_input(self, input: Input, label_length):
        schema = self.schema[input.name]

        label = schema["title"].rjust(label_length)

        delegate = create_input_delegate(input, schema)
        if input.name in self.data:
            value = delegate.display_value(self.data[input.name])
        elif input.default != undefined:
            value = f"<default: {delegate.display_value(input.default)}"
            if not input.empty and not input.default:
                value += ", required"
            value += ">"
        else:
            value = "<not set"
            if input.required:
                value += ", required"
            value += ">"

        return MenuItem(
            text=f" {label}: {value}",
            handler=lambda: self._handle_input(input),
        )

    def _handle_input(self, input: Input):
        self.app.exit(AppResult(
            app=self._create_input_app(input),
            app_result_handler=lambda value: self._handle_input_value(input, value),
        ))

    def _create_input_app(self, input: Input):
        schema = self.schema[input.name]

        value = self.data.get(input.name, undefined)

        return create_input_delegate(input, schema).create_input_app(self.title, schema["title"], value)

    def _handle_input_value(self, input, value):
        schema = self.schema[input.name]

        data = self.data.copy()

        if value is not None:
            if value == undefined:
                data.pop(input.name, None)
            else:
                data[input.name] = create_input_delegate(input, schema).handle_value(value)

        return self._with_data(data, input)

    def _save(self):
        def pre_handler():
            data = {}
            for step in itertools.count(1):
                meth = getattr(self, f"step{step}", None)
                if meth is None:
                    break

                step_widgets = meth(self.data)
                step_inputs = list(filter(lambda w: isinstance(w, Input), step_widgets))
                for input in step_inputs:
                    if input.name in self.data:
                        data[input.name] = self.data[input.name]

            self.process_data(data)

            with self.context.get_client() as c:
                try:
                    if self.method == StepsMethod.CREATE:
                        c.call(f"{self.service}.create", data)
                    elif self.method == StepsMethod.UPDATE:
                        c.call(f"{self.service}.update", self.data[self.primary_key], data)
                    elif self.method == StepsMethod.CONFIG:
                        c.call(f"{self.service}.update", data)
                except ValidationErrors as e:
                    return self._with_errors({None: format_validation_errors(e)})
                except ClientException as e:
                    return self._with_errors({None: format_error(self.context, e)})

                return self.back_app

        self.app.exit(AppResult(app_factory=pre_handler))

    def _back(self):
        self.app.exit(self.back_app)

    def process_data(self, data):
        pass


def input_complete(input: Input, data):
    if input.name not in data:
        return not input.required and input.empty

    if not input.empty:
        return bool(data[input.name])

    return True
