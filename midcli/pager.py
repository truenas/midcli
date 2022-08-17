# -*- coding=utf-8 -*-
import logging

import click

logger = logging.getLogger(__name__)

__all__ = ["enable_pager", "echo_via_pager"]

pager = False


def enable_pager():
    global pager
    pager = True


def echo_via_pager(text):
    if pager:
        click.echo_via_pager(text)
    else:
        print(text)
