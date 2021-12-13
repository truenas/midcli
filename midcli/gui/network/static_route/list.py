# -*- coding=utf-8 -*-
import logging

from midcli.gui.base.list.list import List

from .create_update import StaticRouteCreate, StaticRouteUpdate

logger = logging.getLogger(__name__)

__all__ = ["StaticRouteList"]


class StaticRouteList(List):
    title = "Static Routes"
    item_name = "static route"
    item_title_key = "destination"

    service = "staticroute"
    columns = ["destination", "gateway", "description"]

    create_class = StaticRouteCreate
    update_class = StaticRouteUpdate
