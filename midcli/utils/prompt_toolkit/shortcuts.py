# -*- coding=utf-8 -*-
import logging
from typing import Optional

from prompt_toolkit.application import Application
from prompt_toolkit.application.current import get_app
from prompt_toolkit.formatted_text import AnyFormattedText
from prompt_toolkit.shortcuts.dialogs import _create_app
from prompt_toolkit.styles import BaseStyle
from prompt_toolkit.widgets import (
    Button,
    Dialog,
    Label,
)

logger = logging.getLogger(__name__)

__all__ = ["yes_no_dialog"]


# Copy-pasted from `from prompt_toolkit.shortcuts import yes_no_dialog`
def yes_no_dialog(
    title: AnyFormattedText = "",
    text: AnyFormattedText = "",
    yes_text: str = "Yes",
    no_text: str = "No",
    style: Optional[BaseStyle] = None,
) -> Application[bool]:
    """
    Display a Yes/No dialog.
    Return a boolean.
    """

    def yes_handler() -> None:
        get_app().exit(result=True)

    def no_handler() -> None:
        get_app().exit(result=False)

    dialog = Dialog(
        title=title,
        body=Label(text=text, dont_extend_height=True),
        buttons=[
            Button(text=yes_text, handler=yes_handler, width=len(yes_text) + 2),
            Button(text=no_text, handler=no_handler, width=len(no_text) + 2),
        ],
        with_background=True,
    )

    return _create_app(dialog, style)
