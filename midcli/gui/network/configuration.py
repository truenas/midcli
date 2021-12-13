# -*- coding=utf-8 -*-
import logging

from midcli.gui.base.steps.header import Header
from midcli.gui.base.steps.input import Input
from midcli.gui.base.steps.steps import Steps, StepsMethod

logger = logging.getLogger(__name__)

__all__ = ["NetworkConfiguration"]


class NetworkConfiguration(Steps):
    title = "Network Configuration"

    service = "network.configuration"

    method = StepsMethod.CONFIG

    def step1(self, data):
        return list(filter(None, [
            Header("Network Configuration"),
            Input("hostname"),
            Input("domain"),
            Input("ipv4gateway"),
            Input("ipv6gateway"),
            Input("nameserver1"),
            Input("nameserver2"),
            Input("nameserver3"),
        ]))
