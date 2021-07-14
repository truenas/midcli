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

        try:
            subprocess.run([EDITOR, f.name])
        except FileNotFoundError:
            input(f"EDITOR={EDITOR} not found. Press any key to continue.")
            return ""

        with open(f.name, encoding="utf-8") as fr:
            return fr.read()
