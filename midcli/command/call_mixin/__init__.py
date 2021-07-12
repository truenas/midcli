# -*- coding=utf-8 -*-
import copy
import logging
import traceback

from middlewared.client import ClientException, ValidationErrors

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

    def call(self, name, *args, job=False, raise_=False):
        try:
            args = self._process_call_args(copy.deepcopy(args))

            with self.context.get_client() as c:
                rv = c.call(name, *args, job=job, callback=self._job_callback)

            for op in self.output_processors:
                rv = op(self.context, rv)
        except Exception as e:
            if raise_:
                raise

            if isinstance(e, ValidationErrors):
                print("Validation errors:\n" +
                      "\n".join([f"* {error.attribute}: {error.errmsg}" for error in e.errors]))
            elif isinstance(e, ClientException):
                print(e.trace["formatted"])
            else:
                traceback.print_exc()
        else:
            if self.output:
                print(self.context.display_mode_manager.mode.display(rv))

            return rv

    def _job_callback(self, job):
        description = job["progress"]["description"]

        if description is not None and description != self.job_last_printed_description:
            print(description)

        self.job_last_printed_description = description
