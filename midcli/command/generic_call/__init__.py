# -*- coding=utf-8 -*-
import logging

from prompt_toolkit.shortcuts import yes_no_dialog

from middlewared.client import ClientException, ValidationErrors

from midcli.command.call_mixin import CallMixin
from midcli.command.common_syntax.argument import Argument, BooleanArgument, EnumArgument
from midcli.command.common_syntax.command import CommonSyntaxCommand
from midcli.editor.edit_yaml import edit_yaml
from midcli.utils.lang import undefined

logger = logging.getLogger(__name__)

__all__ = ["GenericCallCommand"]


class CallArgsError(ValueError):
    pass


class GenericCallCommand(CallMixin, CommonSyntaxCommand):
    def __init__(self, *args, method=None, splice_kwargs=None, **kwargs):
        self.method = method
        self.splice_kwargs = splice_kwargs

        self.arguments = []
        self._create_arguments()

        super().__init__(*args, **kwargs)

    def _create_arguments(self):
        for i, item in enumerate(self.method["accepts"] or []):
            if i == self.splice_kwargs:
                if item["type"] != "object":
                    raise ValueError(f"For {self.method['name']!r} specified splice_kwargs={self.splice_kwargs} "
                                     f"for an item of type={item['type']!r}")

                for property_name in item["_attrs_order_"]:
                    self.arguments.append(self._create_argument(item["properties"][property_name]))
            else:
                self.arguments.append(self._create_argument(item))

    def _create_argument(self, item):
        name = item["_name_"]
        nullable = False

        type = item.get("type")
        if isinstance(type, list) and len(type) == 2 and "null" in type:
            nullable = True
            type = [x for x in type if x != "null"][0]

        default = item.get("default", undefined)

        args = (name, nullable, default)
        if type == "boolean":
            return BooleanArgument(*args)
        if "enum" in item:
            return EnumArgument(*args, enum=item["enum"])
        else:
            return Argument(*args)

    def _call_args(self, args, kwargs):
        args = args.copy()

        if self.splice_kwargs is not None:
            if len(args) < self.splice_kwargs:
                raise CallArgsError(f"Too few positional arguments ({self.splice_kwargs} required, "
                                    f"{len(args)} given)")

            if len(args) > self.splice_kwargs:
                raise CallArgsError(f"Too many positional arguments ({self.splice_kwargs} supported, "
                                    f"{len(args)} given)")

            args.append(kwargs)

        return args

    def run(self, args, kwargs):
        if self._is_interactive(args, kwargs):
            self._run_interactive(args, kwargs)
        else:
            self._run_noninteractive(args, kwargs)

    def _is_interactive(self, args, kwargs):
        return self.method["accepts"] and not (args or kwargs)

    def _run_interactive(self, args, kwargs):
        self._run_editor([], [])

    def _run_editor(self, values, errors, method=None):
        while True:
            values = edit_yaml(method or self.method, values, errors)
            if values is None:
                print("Aborted.")
                return

            try:
                self.call(self.method["name"], *values, job=self.method["job"], raise_=True)
                return
            except ValidationErrors as e:
                errors = e.errors
                if yes_no_dialog(
                    title="Validation Errors",
                    text="\n".join([f"* {error.attribute}: {error.errmsg}" for error in errors]) + "\n\nContinue?",
                ).run():
                    continue
                else:
                    print("Aborted.")
                    return
            except ClientException as e:
                if yes_no_dialog(
                    title="Error",
                    text=f"{e.error}.\nContinue?",
                ).run():
                    continue
                else:
                    print("Aborted.")
                    return

    def _run_noninteractive(self, args, kwargs):
        try:
            call_args = self._call_args(args, kwargs)
        except CallArgsError as e:
            print(e.args[0])
            return

        self.call(self.method["name"], *call_args, job=self.method["job"])
