# -*- coding=utf-8 -*-
import logging
import os
import subprocess
import tempfile

logger = logging.getLogger(__name__)

__all__ = ["run_editor"]

EDITOR = os.environ.get("EDITOR", "mcedit")


def run_editor(text):
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", prefix="midcli-") as f:
        f.write(text)
        f.flush()

        subprocess.run([EDITOR, f.name])

        with open(f.name, encoding="utf-8") as fr:
            return fr.read()
