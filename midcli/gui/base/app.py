# -*- coding=utf-8 -*-
from dataclasses import dataclass
import logging
from typing import Callable

logger = logging.getLogger(__name__)

__all__ = ["AppResult", "run_app"]


@dataclass
class AppResult:
    app_factory: Callable = None
    app: object = None
    app_result_handler: Callable = None


def run_app(app):
    while True:
        app = app.run()
        if app is None:
            break

        while isinstance(app, AppResult):
            if app.app_factory:
                app = app.app_factory()
            elif app.app_result_handler:
                app = app.app_result_handler(app.app.run())

        if app is None:
            break
