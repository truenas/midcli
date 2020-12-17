# -*- coding=utf-8 -*-
import logging

logger = logging.getLogger(__name__)

__all__ = ["DisplayModeManager"]


class DisplayModeManager:
    def __init__(self, modes, default_mode):
        self.modes = modes

        self.mode_name = None
        self.mode = None
        self.set_mode(default_mode)

    def set_mode(self, mode_name):
        if mode_name not in self.modes:
            raise ValueError("Mode should be one of: %s" % (", ".join(sorted(self.modes.keys()))))

        self.mode_name = mode_name
        self.mode = self.modes[mode_name]()
