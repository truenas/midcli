# -*- coding=utf-8 -*-
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

    def step1(self, data):
        with self.context.get_client() as c:
            failover_licensed = c.call("failover.licensed")

        result = [Header("Interface Settings")]

        if self.method == StepsMethod.CREATE:
            result.append(Input("type"))

        result.extend([
            Input("name"),
            Input("description"),
        ])
        if not failover_licensed:
            result.extend([
                Input("ipv4_dhcp"),
                Input("ipv6_auto"),
            ])
        result.extend([
            Input("aliases", delegate=AliasesInputDelegate),
        ])
        if failover_licensed:
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
        with self.context.get_client() as c:
            failover_licensed = c.call("failover.licensed")

            if failover_licensed:
                data["ipv4_dhcp"] = False
                data["ipv6_auto"] = False


class NetworkInterfaceUpdate(NetworkInterfaceCreate):
    title = "Update Network Interface"

    method = StepsMethod.UPDATE
