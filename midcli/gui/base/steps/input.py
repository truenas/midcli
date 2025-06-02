# -*- coding=utf-8 -*-
from dataclasses import dataclass
import logging

from midcli.utils.lang import undefined

logger = logging.getLogger(__name__)

__all__ = ["Input"]


@dataclass
class Input:
    name: str
    default: str = undefined
    empty: bool = undefined
    enum: list = undefined
    required: bool = undefined
    delegate: object = None
