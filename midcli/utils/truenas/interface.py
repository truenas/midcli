# -*- coding=utf-8 -*-
import ipaddress
import logging

logger = logging.getLogger(__name__)

__all__ = ["alias_to_str", "str_to_alias"]


def alias_to_str(alias):
    return (
        alias["address"]
        if {"INET": 32, "INET6": 128}[alias["type"]] == alias["netmask"]
        else f"{alias['address']}/{alias['netmask']}"
    )


def str_to_alias(alias):
    ip_network = ipaddress.ip_network(alias, strict=False)

    if isinstance(ip_network, ipaddress.IPv4Network):
        return {
            "type": "INET",
            "address": alias.split("/")[0],
            "netmask": ip_network.prefixlen,
        }

    if isinstance(ip_network, ipaddress.IPv6Network):
        return {
            "type": "INET6",
            "address": alias.split("/")[0],
            "netmask": ip_network.prefixlen,
        }

    raise ValueError(f"Unknown address type: {ip_network!r}")

