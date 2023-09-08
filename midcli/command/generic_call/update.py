# -*- coding=utf-8 -*-
import copy
import logging

from midcli.command.interface import ProcessInputError
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

    def _run_with_editor(self, args):
        method = copy.deepcopy(self.method)

        schema = method["accepts"][1]
        for property in schema["properties"].values():
            property["_required_"] = False

        if len(args.args) == 0:
            key = self.method["accepts"][0]["_name_"]
            try:
                args.args = [args.kwargs.pop(key)]
            except KeyError:
                raise ProcessInputError("Please specify object ID")

        key = args.args[0]
        object = self._call_util(".".join(self.method["name"].split(".")[:-1] + ["get_instance"]),
                                 self._get_instance_call_arg(args.args[0]))

        for name, property in schema["properties"].items():
            if name in object:
                property["default"] = property_to_yaml_arg(property, object[name])

        values = [key, {}]
        errors = []

        self._run_editor(values, errors, self._call_kwargs(args), method)

    def _get_instance_call_arg(self, arg):
        """
        Accepts first argument for update command.
        Returns argument that will be passed to get_instance when retrieving existing row.
        """
        return arg
