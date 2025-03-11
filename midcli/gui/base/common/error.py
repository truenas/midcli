# -*- coding=utf-8 -*-
import logging
import textwrap

from prompt_toolkit.shortcuts import message_dialog

from truenas_api_client import ClientException

from midcli.context import Context
from midcli.gui.base.app import AppResult
from midcli.middleware import format_error

logger = logging.getLogger(__name__)

__all__ = ["gui_handle_error"]


def gui_handle_error(context: Context, error: ClientException, handler):
    return AppResult(
        app=message_dialog("Error", "\n".join(textwrap.wrap(format_error(context, error), 74))),
        app_result_handler=handler,
    )
