# -*- coding=utf-8 -*-
from dataclasses import dataclass
import logging
from typing import TYPE_CHECKING, Callable

from midcli.utils.lang import undefined
if TYPE_CHECKING:
    from midcli.gui.base.steps.input_delegate import InputDelegate

logger = logging.getLogger(__name__)

__all__ = ["Input"]


@dataclass
class Input:
    name: str
    default: str = undefined
    empty: bool = undefined
    enum: list = undefined
    required: bool = undefined
    delegate: Callable[[], "InputDelegate"] | None = None
