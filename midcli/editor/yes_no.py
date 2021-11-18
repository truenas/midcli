# -*- coding=utf-8 -*-
import logging

from midcli.utils.prompt_toolkit.widgets.shortcuts import yes_no_dialog

logger = logging.getLogger(__name__)

__all__ = ["editor_yes_no_dialog"]


def editor_yes_no_dialog(title, text):
    return yes_no_dialog(
        title=title,
        text=text.rstrip("\n") + "\n\nWould you like to open editor and correct this error or quit the process?",
        yes_text="Open Editor",
        no_text="Quit Process",
    )
