# -*- coding=utf-8 -*-
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

__all__ = ["Error"]


@dataclass
class Error:
    title: str
