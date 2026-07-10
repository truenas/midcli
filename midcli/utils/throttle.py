# -*- coding=utf-8 -*-
import time

__all__ = ["Throttler"]


class Throttler:
    """
    Prevents a tight loop from spinning the CPU when its body keeps returning
    immediately (e.g. a prompt that gets EOF/empty input repeatedly).

    The first `burst` calls to `throttle()` return immediately. After that, each
    call sleeps for `delay` seconds. If more than `reset_after` seconds elapse
    between two consecutive calls, the throttle is reset and the next `burst`
    calls are instantaneous again.

    `discard_callback` is called once after every sleep, unless the caller
    passes `discard=False`. It is meant to discard whatever input piled up while
    we were sleeping (e.g. prompt_toolkit's typeahead buffer when a key is held
    down), so the caller doesn't replay a backlog the moment the key is
    released.
    """

    def __init__(self, *, burst=10, delay=0.1, reset_after=1.0, discard_callback=None,
                 monotonic=time.monotonic, sleep=time.sleep):
        self.burst = burst
        self.delay = delay
        self.reset_after = reset_after
        self._discard_callback = discard_callback
        self._monotonic = monotonic
        self._sleep = sleep
        self._count = 0
        self._last = None

    def throttle(self, discard=True):
        now = self._monotonic()
        if self._last is not None and now - self._last > self.reset_after:
            self._count = 0
        self._last = now

        if self._count >= self.burst:
            self._sleep(self.delay)
            if discard and self._discard_callback is not None:
                self._discard_callback()
        else:
            self._count += 1
