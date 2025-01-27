# -*- coding=utf-8 -*-
import logging
from typing import Generic, List, Optional, Sequence, Tuple, TypeVar

from prompt_toolkit.application.current import get_app
from prompt_toolkit.filters import (
    Condition,
)
from prompt_toolkit.formatted_text import (
    AnyFormattedText,
    StyleAndTextTuples,
    to_formatted_text,
)
from prompt_toolkit.formatted_text.utils import fragment_list_to_text
from prompt_toolkit.key_binding.bindings.focus import focus_next, focus_previous
from prompt_toolkit.key_binding.key_bindings import KeyBindings
from prompt_toolkit.key_binding.key_processor import KeyPressEvent
from prompt_toolkit.keys import Keys
from prompt_toolkit.layout.containers import (
    Container,
    Window,
)
from prompt_toolkit.layout.controls import (
    FormattedTextControl,
)
from prompt_toolkit.layout.margins import (
    ConditionalMargin,
    ScrollbarMargin,
)
from prompt_toolkit.mouse_events import MouseEvent, MouseEventType

from midcli.utils.lang import undefined

__all__ = [
    "RadioList",
    "CheckboxList",
]

logger = logging.getLogger(__name__)

E = KeyPressEvent

_T = TypeVar("_T")


class _DialogList(Generic[_T]):
    """
    Common code for `RadioList` and `CheckboxList`.
    """

    open_character: str = ""
    close_character: str = ""
    container_style: str = ""
    default_style: str = ""
    selected_style: str = ""
    checked_style: str = ""
    multiple_selection: bool = False
    show_scrollbar: bool = True

    def __init__(self, values: Sequence[Tuple[_T, AnyFormattedText]], current_values: Optional[_T] = undefined,
                 current_value: Optional[_T] = undefined) -> None:
        self.values = values
        # current_values will be used in multiple_selection,
        # current_value will be used otherwise.
        self.current_values: List[_T] = []
        self.current_value: _T = undefined
        self._selected_index = 0

        if current_values != undefined:
            indexes = [i for i, (v, _) in enumerate(values) if v in current_values]
            if indexes:
                self._selected_index = indexes[0]
                self.current_values = [values[i][0] for i in indexes]

        if current_value != undefined:
            self._selected_index = [i for i, (v, _) in enumerate(values) if v == current_value][0]
            self.current_value = values[self._selected_index][0]

        # Key bindings.
        kb = KeyBindings()

        @kb.add("up")
        def _up(event: E) -> None:
            if self._selected_index == 0:
                focus_previous(event)
                return

            self._selected_index = max(0, self._selected_index - 1)

        @kb.add("down")
        def _down(event: E) -> None:
            if self._selected_index == len(self.values) - 1:
                focus_next(event)
                return

            self._selected_index = min(len(self.values) - 1, self._selected_index + 1)

        @kb.add("pageup")
        def _pageup(event: E) -> None:
            w = event.app.layout.current_window
            if w.render_info:
                self._selected_index = max(
                    0, self._selected_index - len(w.render_info.displayed_lines)
                )

        @kb.add("pagedown")
        def _pagedown(event: E) -> None:
            w = event.app.layout.current_window
            if w.render_info:
                self._selected_index = min(
                    len(self.values) - 1,
                    self._selected_index + len(w.render_info.displayed_lines),
                )

        @kb.add("enter")
        @kb.add(" ")
        def _click(event: E) -> None:
            self._handle_enter()

            if not self.multiple_selection:
                get_app().exit(result=self.current_value)

        @kb.add(Keys.Any)
        def _find(event: E) -> None:
            # We first check values after the selected value, then all values.
            values = list(self.values)
            for value in values[self._selected_index + 1:] + values:
                text = fragment_list_to_text(to_formatted_text(value[1])).lower()

                if text.startswith(event.data.lower()):
                    self._selected_index = self.values.index(value)
                    return

        # Control and window.
        self.control = FormattedTextControl(
            self._get_text_fragments, key_bindings=kb, focusable=True
        )

        self.window = Window(
            content=self.control,
            style=self.container_style,
            right_margins=[
                ConditionalMargin(
                    margin=ScrollbarMargin(display_arrows=True),
                    filter=Condition(lambda: self.show_scrollbar),
                ),
            ],
            dont_extend_height=True,
        )

    def _handle_enter(self) -> None:
        if self.multiple_selection:
            val = self.values[self._selected_index][0]
            if val in self.current_values:
                self.current_values.remove(val)
            else:
                self.current_values.append(val)
        else:
            self.current_value = self.values[self._selected_index][0]

    def _get_text_fragments(self) -> StyleAndTextTuples:
        def mouse_handler(mouse_event: MouseEvent) -> None:
            """
            Set `_selected_index` and `current_value` according to the y
            position of the mouse click event.
            """
            if mouse_event.event_type == MouseEventType.MOUSE_UP:
                self._selected_index = mouse_event.position.y
                self._handle_enter()

        result: StyleAndTextTuples = []
        for i, value in enumerate(self.values):
            if self.multiple_selection:
                checked = value[0] in self.current_values
            else:
                checked = value[0] == self.current_value
            selected = i == self._selected_index

            style = ""
            if checked:
                style += " " + self.checked_style
            if selected:
                style += " " + self.selected_style
            if not checked and not selected:
                style += self.default_style

            result.append((style, self.open_character))

            if selected:
                result.append(("[SetCursorPosition]", ""))

            if checked:
                result.append((style, "*"))
            else:
                result.append((style, " "))

            result.append((style, self.close_character))
            result.append((style, " "))
            result.extend(to_formatted_text(value[1], style=style))
            result.append(("", "\n"))

        # Add mouse handler to all fragments.
        for i in range(len(result)):
            result[i] = (result[i][0], result[i][1], mouse_handler)

        result.pop()  # Remove last newline.
        return result

    def __pt_container__(self) -> Container:
        return self.window


class RadioList(_DialogList[_T]):
    """
    List of radio buttons. Only one can be checked at the same time.

    :param values: List of (value, label) tuples.
    """

    open_character = "("
    close_character = ")"
    container_style = "class:radio-list"
    default_style = "class:radio"
    selected_style = "class:radio-selected"
    checked_style = "class:radio-checked"
    multiple_selection = False


class CheckboxList(_DialogList[_T]):
    """
    List of checkbox buttons. Several can be checked at the same time.

    :param values: List of (value, label) tuples.
    """

    open_character = "["
    close_character = "]"
    container_style = "class:checkbox-list"
    default_style = "class:checkbox"
    selected_style = "class:checkbox-selected"
    checked_style = "class:checkbox-checked"
    multiple_selection = True
