# -*- coding=utf-8 -*-
import copy
import logging
import re
import traceback

from middlewared.client import ClientException, ValidationErrors

from midcli.command.interface import ProcessInputError

logger = logging.getLogger(__name__)

__all__ = ["CallMixin"]


class CallMixin(object):
    output_processors = []

    def __init__(self, *args, **kwargs):
        self.job_last_printed_description = ""
        self.output = kwargs.pop("output", True)

        super().__init__(*args, **kwargs)

    def _process_call_args(self, args):
        """
        Transforms args before passing them to the middleware (e.g. rename poorly named arguments)
        """
        return args

    def call(self, name, *args, job=False, output_processor=None, raise_=False):
        try:
            args = self._process_call_args(copy.deepcopy(args))

            with self.context.get_client() as c:
                rv = c.call(name, *args, job=job, callback=self._job_callback)

            for op in self.output_processors:
                rv = op(self.context, rv)

            if output_processor is not None:
                rv = output_processor(rv)
        except Exception as e:
            if raise_:
                raise

            if (error := self._handle_error(e)) is not None:
                print(error)
            else:
                traceback.print_exc()
        else:
            if self.output:
                print(self.context.display_mode_manager.mode.display(rv))

            return rv

    def _call_util(self, method, *args, **kwargs):
        with self.context.get_client() as c:
            try:
                return c.call(method, *args, **kwargs)
            except Exception as e:
                if (error := self._handle_error(e)) is not None:
                    raise ProcessInputError(f"Error while calling {method}(*{args!r}, **{kwargs!r}):\n{error}")

                raise

    def _handle_error(self, e):
        if isinstance(e, ValidationErrors):
            return ("Validation errors:\n" +
                    "\n".join([
                        f"* {error.attribute}: {error.errmsg}" if error.attribute else f"* {error.errmsg}"
                        for error in e.errors
                    ]))

        if isinstance(e, ClientException):
            if self.context.stacks:
                return e.trace["formatted"]
            else:
                if e.trace["class"] == "CallError":
                    return "Error: " + e.error.split("] ", 1)[1]
                else:
                    return "Error: " + e.trace["repr"]

        return None

    def _job_callback(self, job):
        description = job["progress"]["description"]

        if description is not None and description != self.job_last_printed_description:
            print(description)

        self.job_last_printed_description = description
