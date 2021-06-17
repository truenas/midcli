# -*- coding=utf-8 -*-
import json
import re
import subprocess


def command_test(command, *, mode="csv", extra_args=None, input=None, text=None, regex=None):
    extra_args = extra_args or []

    if input is not None:
        if not isinstance(input, str):
            input = json.dumps(input)

    stdout = subprocess.run(["cli", "-m", mode, "-c", command] + extra_args, encoding="utf-8", input=input,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout

    if text is not None:
        assert stdout.rstrip() == text, stdout
    elif regex is not None:
        assert re.match(regex, stdout, flags=re.S), stdout
    else:
        assert False
