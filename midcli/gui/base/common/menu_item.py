# -*- coding=utf-8 -*-
import logging
from typing import Callable, Optional

from prompt_toolkit.application.current import get_app
from prompt_toolkit.formatted_text import (
    StyleAndTextTuples,
)
from prompt_toolkit.key_binding.key_bindings import KeyBindings
from prompt_toolkit.key_binding.key_processor import KeyPressEvent
from prompt_toolkit.layout.containers import (
    Container,
    Window,
    WindowAlign,
)
from prompt_toolkit.layout.controls import (
    FormattedTextControl,
)
from prompt_toolkit.mouse_events import MouseEvent, MouseEventType


logger = logging.getLogger(__name__)

__all__ = ["MenuItem"]


class MenuItem:
    def __init__(
        self, text: str, handler: Optional[Callable[[], None]] = None,
    ) -> None:
        self.text = text
        self.handler = handler
        self.control = FormattedTextControl(
            self._get_text_fragments,
            key_bindings=self._get_key_bindings(),
            focusable=True,
        )

        def get_style() -> str:
            if get_app().layout.has_focus(self):
                return "class:button.focused"
            else:
                return "class:button"

        self.window = Window(
            self.control,
            height=len(text.split("\n")),
            align=WindowAlign.LEFT,
            style=get_style,
        )

    def _get_text_fragments(self) -> StyleAndTextTuples:
        text = self.text

        def handler(mouse_event: MouseEvent) -> None:
            if (
                self.handler is not None and
                mouse_event.event_type == MouseEventType.MOUSE_UP
            ):
                self.handler()

        return [
            ("class:button.text", text, handler),
        ]

    def _get_key_bindings(self) -> KeyBindings:
        " Key bindings for the Button. "
        kb = KeyBindings()

        @kb.add(" ")
        @kb.add("enter")
        def _(event: KeyPressEvent) -> None:
            if self.handler is not None:
                self.handler()

        return kb

    def __pt_container__(self) -> Container:
        return self.window
