# -*- coding=utf-8 -*-
from dataclasses import dataclass, field
import logging

from midcli.utils.lang import undefined

logger = logging.getLogger(__name__)

__all__ = ["Input"]


@dataclass
class Input:
    name: str
    default: str = undefined
    empty: bool = undefined
    enum: list = field(default_factory=list)
    required: bool = undefined
    delegate: object = None
