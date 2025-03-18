# -*- coding=utf-8 -*-
import functools
import logging
import textwrap

from prompt_toolkit.application import get_app
from prompt_toolkit.filters import has_focus
from prompt_toolkit.key_binding.bindings.focus import focus_next, focus_previous
from prompt_toolkit.key_binding.key_bindings import KeyBindings
from prompt_toolkit.layout.containers import (
    AnyContainer,
    HSplit,
)
from prompt_toolkit.shortcuts import yes_no_dialog
from prompt_toolkit.shortcuts.dialogs import _create_app
from prompt_toolkit.widgets import Label
from prompt_toolkit.widgets.base import Box, Frame, Shadow

from truenas_api_client import ClientException

from midcli.display_mode.mode.text_mixin import TextMixin
from midcli.gui.base.app import AppResult
from midcli.gui.base.common.error import gui_handle_error
from midcli.gui.base.common.menu_item import MenuItem

logger = logging.getLogger(__name__)

__all__ = ["List"]


class List:
    title = NotImplemented
    item_name = NotImplemented
    item_title_key = NotImplemented

    service = NotImplemented
    primary_key = "id"
    columns = NotImplemented
    columns_processors = {}

    create_class = None
    update_class = NotImplemented
    deletable = True

    def __init__(self, context):
        self.context = context

        with context.get_client() as c:
            self.data = c.call(f"{self.service}.query")

        self.kb = KeyBindings()
        actions = []
        if self.data:
            actions.append(f"<Enter> to edit a {self.item_name}")
            if self.deletable:
                actions.append(f"<Delete> to delete a {self.item_name}")
                self.kb.add("delete")(self._delete_handler)
        if self.create_class:
            actions.append(f"<n> to create a new {self.item_name}")
            self.kb.add("n")(
                lambda event: event.app.exit(
                    self.create_class(
                        self.context,
                        AppResult(app_factory=lambda: self.__class__(self.context))
                    )
                )
            )
        actions.append("<r> to refresh")
        self.kb.add("r")(lambda event: event.app.exit(AppResult(app_factory=lambda: self.__class__(self.context))))
        actions.append("<q> to quit")
        self.kb.add("q")(lambda event: event.app.exit(None))

        help_label = Label("\n" + "\n".join(textwrap.wrap(f"Press {', '.join(actions)}.", width=60)))

        if self.data:
            header, rows, footer = self._draw(self.data)

            header_label = Label(header)
            self.row_labels = [
                MenuItem(row, handler=functools.partial(self._edit_handler, self.data[i]))
                for i, row in enumerate(rows)
            ]
            footer_label = Label(footer)

            inputs_kb = KeyBindings()
            first_input_selected = has_focus(self.row_labels[0])
            last_input_selected = has_focus(self.row_labels[-1])
            inputs_kb.add("up", filter=first_input_selected)(lambda event: event.app.layout.focus(self.row_labels[-1]))
            inputs_kb.add("up", filter=~first_input_selected)(focus_previous)
            inputs_kb.add("down", filter=last_input_selected)(lambda event: event.app.layout.focus(self.row_labels[0]))
            inputs_kb.add("down", filter=~last_input_selected)(focus_next)

            self.no_rows_label = None
            widgets = [header_label] + self.row_labels + [footer_label]
        else:
            self.row_labels = []

            inputs_kb = None

            self.no_rows_label = Label(f"No {self.item_name} found.")
            widgets = [self.no_rows_label]

        self.hsplit = HSplit(widgets + [help_label], padding=0, key_bindings=inputs_kb)
        frame_body = HSplit(
            [
                Box(
                    body=self.hsplit,
                ),
            ]
        )

        frame = Shadow(
            body=Frame(
                title=lambda: self.title,
                body=frame_body,
                style="class:dialog.body",
                width=None,
                key_bindings=self.kb,
                modal=True,
            )
        )

        self.container = Box(body=frame, style="class:dialog", width=None)

        self.app = None

    def __pt_container__(self) -> AnyContainer:
        return self.container

    def run(self):
        self.app = _create_app(self, None)
        self._setup_app()
        if self.no_rows_label:
            self.app.layout.focus(self.no_rows_label)
        return self.app.run()

    def _draw(self, data):
        col_width = [len(col) for col in self.columns]
        rows = []
        row_line_count = []
        for item in data:
            row = []
            line_count = 1
            for i, col in enumerate(self.columns):
                if col in self.columns_processors:
                    val = self.columns_processors[col](item)
                else:
                    val = item
                    for k in col.split("."):
                        val = val[k]

                    val = TextMixin().value_to_text(val)

                lines = val.split("\n")
                row.append(lines)

                col_width[i] = max(col_width[i], max(map(len, lines)))

                line_count = max(line_count, len(lines))

            rows.append(row)
            row_line_count.append(line_count)

        border = "".join(f"+{''.rjust(width + 2, '-')}" for col, width in zip(self.columns, col_width)) + "+"

        header = (
            f"{border}\n" +
            "".join(f"| {col.rjust(width)} " for col, width in zip(self.columns, col_width)) + "|\n" +
            border
        )

        rendered_rows = []
        for row, line_count in zip(rows, row_line_count):
            rendered_row = [""] * line_count
            for i in range(line_count):
                for j, (col, width) in enumerate(zip(self.columns, col_width)):
                    rendered_row[i] += f"| {(row[j][i] if i < len(row[j]) else '').rjust(width)} "
                rendered_row[i] += "|"
            rendered_rows.append("\n".join(rendered_row))

        footer = border

        return header, rendered_rows, footer

    def _edit_handler(self, row):
        get_app().exit(
            self.update_class(
                self.context,
                AppResult(app_factory=lambda: self.__class__(self.context)),
                data=row
            )
        )

    def _delete_handler(self, event):
        if row := self._focused_row():
            def handler(sure):
                if sure:
                    with self.context.get_client() as c:
                        try:
                            c.call(f"{self.service}.delete", row[self.primary_key])
                        except ClientException as e:
                            return gui_handle_error(self.context, e, lambda _: self.__class__(self.context))

                return self.__class__(self.context)

            event.app.exit(AppResult(
                app=yes_no_dialog(
                    f"Delete {self.item_name}",
                    f"Are you sure want to delete {self.item_name} {row[self.item_title_key]!r}?"
                ),
                app_result_handler=handler,
            ))

    def _focused_row(self):
        for row, label in zip(self.data, self.row_labels):
            if get_app().layout.has_focus(label):
                return row

    def _setup_app(self):
        pass
