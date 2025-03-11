# -*- coding=utf-8 -*-
import asyncio
import logging

from prompt_toolkit.filters import Condition
from prompt_toolkit.layout.containers import ConditionalContainer, to_container
from prompt_toolkit.widgets import Label

from truenas_api_client import ClientException

from midcli.gui.base.app import AppResult
from midcli.gui.base.common.error import gui_handle_error
from midcli.gui.base.list.list import List
from midcli.utils.truenas.interface import alias_to_str

from .create_update import NetworkInterfaceCreate, NetworkInterfaceUpdate

logger = logging.getLogger(__name__)

__all__ = ["NetworkInterfaceList"]


class NetworkInterfaceList(List):
    title = "Network Interfaces"
    item_name = "network interface"
    item_title_key = "name"

    service = "interface"
    columns = ["name", "aliases", "state.aliases"]
    columns_processors = {
        "aliases": lambda interface: "\n".join([
            alias_to_str(alias)
            for alias in interface["aliases"]
        ]),
        "state.aliases": lambda interface: "\n".join([
            alias_to_str(alias)
            for alias in interface["state"]["aliases"]
            if alias["type"] in ["INET", "INET6"]
        ]),
    }

    create_class = NetworkInterfaceCreate
    update_class = NetworkInterfaceUpdate

    def _setup_app(self):
        label = Label("", style="bg:black fg:white")
        cc = ConditionalContainer(label, Condition(lambda: label.text != ""))

        self.hsplit.children.append(to_container(Label("")))
        self.hsplit.children.append(to_container(cc))

        self.kb.add("a")(lambda event: event.app.exit(AppResult(app_factory=apply_app_factory)))
        self.kb.add("p")(lambda event: event.app.exit(AppResult(app_factory=persist_app_factory)))

        def apply_app_factory():
            print("Applying network interface changes...")
            with self.context.get_client() as c:
                try:
                    c.call("interface.commit")
                except ClientException as e:
                    return gui_handle_error(self.context, e, lambda _: NetworkInterfaceList(self.context))

            return NetworkInterfaceList(self.context)

        def persist_app_factory():
            with self.context.get_client() as c:
                c.call("interface.checkin")

            return NetworkInterfaceList(self.context)

        def get_text():
            with self.context.get_client() as c:
                if checkin_waiting := c.call("interface.checkin_waiting"):
                    n = int(checkin_waiting)
                    return (
                        f"Network interface changes have been applied.\n"
                        f"Press <p> to persist them if the network is still operational\n"
                        f"or they will be rolled back in {n} seconds."
                    )
                elif c.call("interface.has_pending_changes"):
                    return (
                        "You have pending network interface changes.\n"
                        "Press <a> to apply them."
                    )

        async def refresh():
            while True:
                label.text = await asyncio.get_running_loop().run_in_executor(None, get_text) or ""

                self.app.invalidate()

                await asyncio.sleep(1)

        self.app.pre_run_callables.append(lambda: self.app.create_background_task(refresh()))
