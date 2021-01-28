# -*- coding=utf-8 -*-
import copy
import logging

from midcli.editor.yaml.object import property_to_yaml_arg

from . import GenericCallCommand

logger = logging.getLogger(__name__)

__all__ = ["UpdateCommand"]


class UpdateCommand(GenericCallCommand):
    def _is_interactive(self, args, kwargs):
        return len(args) < 2 and len(kwargs) == 0

    def _run_interactive(self, args, kwargs):
        method = copy.deepcopy(self.method)

        schema = method["accepts"][1]
        for property in schema["properties"].values():
            property["_required_"] = False

        if len(args) == 1:
            key = args[0]
            with self.context.get_client() as c:
                object = c.call(".".join(self.method["name"].split(".")[:-1] + ["get_instance"]), key)

            for name, property in schema["properties"].items():
                if name in object:
                    property["default"] = property_to_yaml_arg(property, object[name])

            values = [key, {}]
            errors = []
        else:
            values = []
            errors = []

        self._run_editor(values, errors, method)
