# -*- coding=utf-8 -*-
import functools
import logging

from midcli.gui.base.steps.header import Header
from midcli.gui.base.steps.input import Input
from midcli.gui.base.steps.steps import Steps, StepsMethod

from .input_delegate import AliasesInputDelegate

logger = logging.getLogger(__name__)

__all__ = ["NetworkInterfaceCreate", "NetworkInterfaceUpdate"]


class NetworkInterfaceCreate(Steps):
    title = "Create Network Interface"

    service = "interface"

    method = StepsMethod.CREATE

    @functools.cached_property
    def failover_licensed(self):
        # A new `Steps` is built for every redraw, so this is re-fetched whenever the form
        # is redrawn, and at most once per instance.
        with self.context.get_client() as c:
            return c.call("failover.licensed")

    def step1(self, data):
        result = [Header("Interface Settings")]

        if self.method == StepsMethod.CREATE:
            result.append(Input("type"))

        result.extend([
            Input("name"),
            Input("description"),
        ])
        if not self.failover_licensed:
            result.extend([
                Input("ipv4_dhcp"),
                Input("ipv6_auto"),
            ])
        result.extend([
            Input("aliases", delegate=AliasesInputDelegate),
        ])
        if self.failover_licensed:
            result.extend([
                Header("Failover Settings"),
                Input("failover_critical"),
                Input("failover_group"),
                Input("failover_aliases", delegate=lambda: AliasesInputDelegate(netmask=False)),
                Input("failover_virtual_aliases", delegate=lambda: AliasesInputDelegate(netmask=False)),
            ])

        return result

    def step2(self, data):
        with self.context.get_client() as c:
            result = []

            if data["type"] == "BRIDGE":
                result.append(Header("Bridge Settings"))
                result.append(Input("bridge_members",
                                    enum=c.call("interface.bridge_members_choices", data.get("name")),
                                    empty=False))
            elif data["type"] == "LINK_AGGREGATION":
                result.append(Header("Link Aggregation Settings"))
                result.append(Input("lag_protocol", required=True))
                result.append(Input("lag_ports",
                                    enum=c.call("interface.lag_ports_choices", data.get("name")),
                                    empty=False))
                result.append(Input("xmit_hash_policy"))
                result.append(Input("lacpdu_rate"))
            elif data["type"] == "VLAN":
                result.append(Header("VLAN Settings"))
                result.append(Input("vlan_parent_interface",
                                    enum=c.call("interface.vlan_parent_interface_choices"),
                                    required=True))
                result.append(Input("vlan_tag", required=True))
                result.append(Input("vlan_pcp"))

            result.extend([
                Header("Other Settings"),
                Input("mtu"),
            ])

            return result

    def process_data(self, data):
        if self.failover_licensed:
            data["ipv4_dhcp"] = False
            data["ipv6_auto"] = False

            # `interface.query` reports failover aliases with a `netmask`, but
            # `interface.create`/`interface.update` reject it. Values the user did not
            # retype reach us verbatim from the query, so strip it before submitting.
            # Rebuild rather than mutate: these dicts are shared with `self.data`.
            for key in ("failover_aliases", "failover_virtual_aliases"):
                if aliases := data.get(key):
                    data[key] = [
                        {k: v for k, v in alias.items() if k != "netmask"}
                        for alias in aliases
                    ]


class NetworkInterfaceUpdate(NetworkInterfaceCreate):
    title = "Update Network Interface"

    method = StepsMethod.UPDATE
