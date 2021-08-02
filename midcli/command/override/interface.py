# -*- coding=utf-8 -*-
import errno
import logging

import ipaddress

from middlewared.client import ClientException, ValidationErrors

from midcli.command.generic_call import GenericCallCommand

logger = logging.getLogger(__name__)

__all__ = ["InterfaceCreateCommand", "InterfaceUpdateCommand"]


class InterfaceCommandMixin:
    def _process_interface(self, interface, schema):
        errors = []

        if "aliases" in interface:
            if isinstance(interface["aliases"], list):
                aliases = []
                for i, alias in enumerate(interface["aliases"]):
                    try:
                        aliases.append(self._process_alias(alias))
                    except Exception as e:
                        errors.append((f"{schema}.aliases.{i}", str(e), errno.EINVAL))

                interface["aliases"] = aliases

        if errors:
            raise ValidationErrors(errors)

        return interface

    def _process_alias(self, alias):
        if isinstance(alias, str):
            return self._string_alias_to_object(alias)

        return alias

    def _string_alias_to_object(self, alias):
        ip_network = ipaddress.ip_network(alias, strict=False)

        if isinstance(ip_network, ipaddress.IPv4Network):
            return {
                "type": "INET",
                "address": str(ip_network.network_address),
                "netmask": ip_network.prefixlen,
            }

        if isinstance(ip_network, ipaddress.IPv6Network):
            return {
                "type": "INET6",
                "address": str(ip_network.network_address),
                "netmask": ip_network.prefixlen,
            }

        raise ValueError(f"Unknown address type: {ip_network!r}")


class InterfaceCreateCommand(InterfaceCommandMixin, GenericCallCommand):
    def _process_call_args(self, values):
        values = list(values)
        if values:
            values[0] = self._process_interface(values[0], "interface_create")
        return values


class InterfaceUpdateCommand(InterfaceCommandMixin, GenericCallCommand):
    def _process_call_args(self, values):
        values = list(values)
        if values and len(values) > 1:
            values[1] = self._process_interface(values[1], "interface_update")
        return values
