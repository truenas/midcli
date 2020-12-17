# -*- coding=utf-8 -*-
import pytest

from midcli.display_mode.mode.base_table import TableDisplayModeBase


@pytest.mark.parametrize("objects,header", [
    ([{"id": 1, "auto": False, "name": "Task 1"},
      {"id": 2, "auto": True, "schedule": "* * *", "name": "Task 2"}],
     ["id", "auto", "schedule", "name"])
])
def test_prepare_header(objects, header):
    assert TableDisplayModeBase()._prepare_header(objects) == header
