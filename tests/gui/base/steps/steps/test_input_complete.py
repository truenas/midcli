# -*- coding=utf-8 -*-
from unittest.mock import Mock

import pytest

from midcli.gui.base.steps.steps import input_complete
from midcli.utils.lang import undefined


@pytest.mark.parametrize("input,data,result", [
    (Mock(name="bridge_members", required=True, empty=False), {}, False),
    (Mock(name="bridge_members", required=True, empty=False), {"bridge_members": []}, False),
    (Mock(name="bridge_members", required=True), {"bridge_members": []}, True),
])
def test_input_complete(input, data, result):
    input.name = input._mock_name

    if not hasattr(input, "empty"):
        input.empty = undefined

    assert input_complete(input, data) == result
