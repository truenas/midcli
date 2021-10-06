# -*- coding=utf-8 -*-
import errno
import ipaddress
import json
import logging

from .utils import remove_fields, rows_processor

from middlewared.client import ClientException, ValidationErrors

from midcli.command.generic_call import GenericCallCommand
from midcli.command.query.command import QueryCommand

logger = logging.getLogger(__name__)

__all__ = ["InterfaceQueryCommand", "InterfaceCreateCommand", "InterfaceUpdateCommand"]

remove_id = remove_fields("id")


@rows_processor
def patch_interface(context, interfaces):
    for i, interface in enumerate(interfaces):
        interface["state.aliases"] = [
            (
                alias["address"]
                if {"INET": 32, "INET6": 128}[alias["type"]] == alias["netmask"]
                else f"{alias['address']}/{alias['netmask']}"
            )
            for alias in interface["state"]["aliases"]
            if alias["type"] in ["INET", "INET6"]
        ]
        interface["aliases"] = [
            (
                alias["address"]
                if {"INET": 32, "INET6": 128}[alias["type"]] == alias["netmask"]
                else f"{alias['address']}/{alias['netmask']}"
            )
            for alias in interface["aliases"]
        ]

        interface.pop("fake")
        interface.pop("state")

        interfaces[i] = {
            "name": interface["name"],
            "type": interface["type"],
            **{k: v for k, v in interface.items() if k.startswith("state.")},
            **{k: v for k, v in interface.items() if not (k in ["name", "type"] or k.startswith("state."))},
        }


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


class InterfaceQueryCommand(QueryCommand):
    output_processors = [remove_id, patch_interface]


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
