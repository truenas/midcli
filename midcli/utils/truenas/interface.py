# -*- coding=utf-8 -*-
import ipaddress
import logging

logger = logging.getLogger(__name__)

__all__ = ["alias_to_str", "str_to_alias"]


def alias_to_str(alias, netmask=True):
    if netmask:
        return f"{alias['address']}/{alias['netmask']}"
    else:
        return alias["address"]


def str_to_alias(alias, netmask=True):
    ip_network = ipaddress.ip_network(alias, strict=False)

    if netmask:
        if "/" not in alias:
            raise ValueError("Please specify the IP address in CIDR notation")
    else:
        if "/" in alias:
            raise ValueError("Please specify single IP address")

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
