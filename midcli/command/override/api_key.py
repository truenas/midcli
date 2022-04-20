# -*- coding=utf-8 -*-
import logging

from midcli.command.generic_call import GenericCallCommand

logger = logging.getLogger(__name__)

__all__ = ["ApiKeyCreateCommand"]


class ApiKeyCreateCommand(GenericCallCommand):
    def _handle_output(self, rv):
        print(f"API Key: {rv['key']}")
