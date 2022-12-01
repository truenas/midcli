# -*- coding=utf-8 -*-
import ipaddress
import logging

logger = logging.getLogger(__name__)

__all__ = ["alias_to_str", "str_to_alias"]


def alias_to_str(alias, netmask=True):
    return (
        alias["address"]
        if not netmask or {"INET": 32, "INET6": 128}[alias["type"]] == alias["netmask"]
        else f"{alias['address']}/{alias['netmask']}"
    )


def str_to_alias(alias, netmask=True):
    ip_network = ipaddress.ip_network(alias, strict=False)

    if isinstance(ip_network, ipaddress.IPv4Network):
        result = {
            "type": "INET",
            "address": alias.split("/")[0],
        }
        if netmask:
            result["netmask"] = ip_network.prefixlen
        return result

    if isinstance(ip_network, ipaddress.IPv6Network):
        result = {
            "type": "INET6",
            "address": alias.split("/")[0],
        }
        if netmask:
            result["netmask"] = ip_network.prefixlen
        return result

    raise ValueError(f"Unknown address type: {ip_network!r}")
