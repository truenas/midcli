# -*- coding=utf-8 -*-
from unittest.mock import MagicMock

import pytest

from midcli.gui.network.interface.create_update import NetworkInterfaceCreate


def steps(failover_licensed=True):
    steps = MagicMock()
    client = MagicMock()
    client.call.return_value = failover_licensed
    steps.context.get_client.return_value.__enter__.return_value = client
    return steps


def test_failover_alias_netmask_is_stripped():
    # `interface.query` reports failover aliases with a `netmask` that `interface.update` rejects.
    queried_failover = [{"type": "INET", "address": "10.217.120.8", "netmask": 25}]
    queried_virtual = [{"type": "INET", "address": "10.217.120.9", "netmask": 32}]
    data = {"failover_aliases": queried_failover, "failover_virtual_aliases": queried_virtual}

    NetworkInterfaceCreate.process_data(steps(), data)

    assert data["failover_aliases"] == [{"type": "INET", "address": "10.217.120.8"}]
    assert data["failover_virtual_aliases"] == [{"type": "INET", "address": "10.217.120.9"}]


def test_failover_aliases_from_query_are_not_mutated():
    # `_save` copies these dicts by reference out of `self.data`, which is redrawn on error.
    queried_failover = [{"type": "INET", "address": "10.217.120.8", "netmask": 25}]
    queried_virtual = [{"type": "INET", "address": "10.217.120.9", "netmask": 32}]

    NetworkInterfaceCreate.process_data(
        steps(), {"failover_aliases": queried_failover, "failover_virtual_aliases": queried_virtual}
    )

    assert queried_failover == [{"type": "INET", "address": "10.217.120.8", "netmask": 25}]
    assert queried_virtual == [{"type": "INET", "address": "10.217.120.9", "netmask": 32}]


def test_aliases_keep_their_netmask():
    data = {"aliases": [{"type": "INET", "address": "10.217.120.7", "netmask": 25}]}

    NetworkInterfaceCreate.process_data(steps(), data)

    assert data["aliases"] == [{"type": "INET", "address": "10.217.120.7", "netmask": 25}]


@pytest.mark.parametrize("data", [{}, {"failover_aliases": [], "failover_virtual_aliases": []}])
def test_absent_or_empty_failover_aliases(data):
    expected = dict(data)

    NetworkInterfaceCreate.process_data(steps(), data)

    for key, value in expected.items():
        assert data[key] == value


def test_unlicensed_data_is_untouched():
    data = {"failover_aliases": [{"type": "INET", "address": "10.217.120.8", "netmask": 25}]}

    NetworkInterfaceCreate.process_data(steps(failover_licensed=False), data)

    assert data == {"failover_aliases": [{"type": "INET", "address": "10.217.120.8", "netmask": 25}]}
