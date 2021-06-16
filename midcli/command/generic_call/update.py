# -*- coding=utf-8 -*-
import copy
import logging

from midcli.editor.yaml.object import property_to_yaml_arg

from . import GenericCallCommand

logger = logging.getLogger(__name__)

__all__ = ["UpdateCommand"]


class UpdateCommand(GenericCallCommand):
    def _needs_editor(self, args, kwargs):
        if self.method["accepts"][0]["_name_"] in kwargs:
            return len(kwargs) == 1

        return len(args) == 1 and len(kwargs) == 0

    def _call_args(self, args, kwargs):
        if len(args) == 0 and self.method["accepts"][0]["_name_"] in kwargs:
            args = [kwargs.pop(self.method["accepts"][0]["_name_"])]

        return super()._call_args(args, kwargs)

    def _run_with_editor(self, args, kwargs):
        method = copy.deepcopy(self.method)

        schema = method["accepts"][1]
        for property in schema["properties"].values():
            property["_required_"] = False

        if len(args) == 0:
            args = [kwargs.pop(self.method["accepts"][0]["_name_"])]

        key = args[0]
        with self.context.get_client() as c:
            object = c.call(".".join(self.method["name"].split(".")[:-1] + ["get_instance"]), key)

        for name, property in schema["properties"].items():
            if name in object:
                property["default"] = property_to_yaml_arg(property, object[name])

        values = [key, {}]
        errors = []

        self._run_editor(values, errors, method)
