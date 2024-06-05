# -*- coding=utf-8 -*-
import copy
import logging
import os
import shutil
import threading
import traceback

import requests

from truenas_api_client import ClientException, ValidationErrors

from midcli.command.interface import ProcessInputError
from midcli.middleware import format_error, format_validation_errors
from midcli.pager import echo_via_pager

logger = logging.getLogger(__name__)

__all__ = ["CallMixin"]


class CallMixin:
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

    def call(self, name, *args, job=False, output_processor=None, pipe_output=None, raise_=False):
        try:
            args = self._process_call_args(copy.deepcopy(args))

            with self.context.get_client() as c:
                if job and pipe_output is not None:
                    if self.context.url and self.context.url.startswith(("ws://", "wss://")):
                        schema, rest = self.context.url.split("://")
                        hostname_port = rest.split("/")[0]
                        http_url = f"http{schema.removeprefix('ws')}://{hostname_port}"
                        verify = True
                    else:
                        http_url = f"http://127.0.0.1:{c.call('system.general.config')['ui_port']}"
                        verify = False

                    with open(pipe_output, "wb") as f:
                        job_id, download_url = c.call("core.download", name, args, pipe_output)
                        download_thread = threading.Thread(
                            daemon=True, target=self._download, args=(http_url + download_url, verify, pipe_output, f),
                        )
                        download_thread.start()
                        rv = c.call("core.job_wait", job_id, job=True, callback=self._job_callback)
                        download_thread.join()
                        print(f"[100%] Job output ({os.path.getsize(pipe_output)} bytes) saved at {pipe_output!r}")
                else:
                    rv = c.call(name, *args, job=job, callback=self._job_callback)

            for op in self.output_processors:
                rv = op(self.context, rv)

            if output_processor is not None:
                rv = output_processor(rv)
        except Exception as e:
            if raise_:
                raise

            if (error := self._handle_error(e)) is not None:
                raise ProcessInputError(error)
            else:
                raise ProcessInputError(traceback.format_exc())
        else:
            self._handle_output(rv)

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
            return (
                "Validation errors:\n" +
                format_validation_errors(e) +
                ("\nHint: Add -- to the end of the command to open an interactive arguments editor"
                 if any(error.errmsg == "attribute required" for error in e.errors) else "")
            )

        if isinstance(e, ClientException):
            return format_error(self.context, e)

        return None

    def _handle_output(self, rv):
        if self.output:
            echo_via_pager(self.context.display_mode_manager.mode.display(rv))

    def _job_callback(self, job):
        text = f"[{int(job['progress']['percent'] or 0)}%] {job['progress']['description']}..."

        if text != self.job_last_printed_description:
            print(text)

        self.job_last_printed_description = text

    def _download(self, url, verify, path, f):
        try:
            with requests.get(url, stream=True, verify=verify) as r:
                r.raise_for_status()
                shutil.copyfileobj(r.raw, f)
        except Exception as e:
            print(f"Error downloading {url!r} to {path!r}: {e!r}")
