# -*- coding=utf-8 -*-
from unittest.mock import Mock

from midcli.utils.throttle import Throttler


def make_throttler(**kwargs):
    """Throttler driven by a virtual clock so tests don't actually sleep."""
    clock = {"now": 0.0}
    sleeps = []
    flushes = []

    def monotonic():
        return clock["now"]

    def sleep(seconds):
        sleeps.append(seconds)

    kwargs.setdefault("discard_callback", lambda: flushes.append(clock["now"]))
    throttler = Throttler(monotonic=monotonic, sleep=sleep, **kwargs)
    throttler._test_flushes = flushes
    return throttler, clock, sleeps


def test_first_burst_calls_do_not_sleep():
    throttler, clock, sleeps = make_throttler(burst=10, delay=0.01)

    for _ in range(10):
        throttler.throttle()

    assert sleeps == []
    # No sleep -> nothing accumulated -> no flush.
    assert throttler._test_flushes == []


def test_calls_after_burst_sleep():
    throttler, clock, sleeps = make_throttler(burst=10, delay=0.01)

    for _ in range(15):
        throttler.throttle()

    # First 10 are instantaneous, the remaining 5 each sleep `delay`.
    assert sleeps == [0.01] * 5
    # Each sleep is followed by a flush of the accumulated input.
    assert len(throttler._test_flushes) == 5


def test_gap_longer_than_reset_resets_throttle():
    throttler, clock, sleeps = make_throttler(burst=10, delay=0.01, reset_after=1.0)

    # Exhaust the burst so the next call would sleep.
    for _ in range(15):
        throttler.throttle()
    assert sleeps == [0.01] * 5

    # More than a second passes between two calls -> throttle resets.
    clock["now"] += 1.5
    sleeps.clear()

    for _ in range(10):
        throttler.throttle()

    assert sleeps == []


def test_gap_within_reset_does_not_reset_throttle():
    throttler, clock, sleeps = make_throttler(burst=10, delay=0.01, reset_after=1.0)

    for _ in range(10):
        throttler.throttle()
    assert sleeps == []

    # Exactly one second is not "more than a second", so no reset.
    clock["now"] += 1.0
    throttler.throttle()

    assert sleeps == [0.01]


def test_discard_callback_runs_after_each_sleep_only():
    discards = []
    throttler, clock, sleeps = make_throttler(
        burst=2, delay=0.01, discard_callback=lambda: discards.append(True),
    )

    # First 2 calls: no sleep, no discard.
    throttler.throttle()
    throttler.throttle()
    assert discards == []

    # 3rd call sleeps and then discards.
    throttler.throttle()
    assert discards == [True]


def test_discard_false_sleeps_without_discarding():
    discards = []
    throttler, clock, sleeps = make_throttler(
        burst=2, delay=0.01, discard_callback=lambda: discards.append(True),
    )

    throttler.throttle()
    throttler.throttle()

    # 3rd call still sleeps but must not discard the accumulated input.
    throttler.throttle(discard=False)
    assert sleeps == [0.01]
    assert discards == []


def test_no_discard_callback_is_fine():
    throttler = Throttler(burst=1, monotonic=lambda: 0.0, sleep=lambda s: None)

    throttler.throttle()
    throttler.throttle()  # would sleep+discard; callback is None, must not raise


def test_uses_real_sleep_and_monotonic_by_default():
    sleep = Mock()
    monotonic = Mock(return_value=0.0)
    throttler = Throttler(burst=1, monotonic=monotonic, sleep=sleep)

    throttler.throttle()
    throttler.throttle()

    sleep.assert_called_once_with(throttler.delay)
