# -*- coding=utf-8 -*-
import logging

from midcli.gui.base.steps.header import Header
from midcli.gui.base.steps.input import Input
from midcli.gui.base.steps.steps import Steps, StepsMethod

logger = logging.getLogger(__name__)

__all__ = ["StaticRouteCreate", "StaticRouteUpdate"]


class StaticRouteCreate(Steps):
    title = "Create Static Route"

    service = "staticroute"

    method = StepsMethod.CREATE

    def step1(self, data):
        return [
            Header("Static Route"),
            Input("destination"),
            Input("gateway"),
            Input("description"),
        ]


class StaticRouteUpdate(StaticRouteCreate):
    title = "Update Static Route"

    method = StepsMethod.UPDATE
