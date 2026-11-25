"""until(): check, then sleep min(every, left), until done(value) or within seconds have passed; time from a clock object."""
import time
from typing import Any, NamedTuple


class Clock:
    """Monotonic seconds and sleep; tests hand in a fake one."""

    def monotonic(self):
        return time.monotonic()

    def sleep(self, seconds):
        time.sleep(seconds)


SYSTEM = Clock()


class Waited(NamedTuple):
    value: Any
    seconds: float
    met: bool


def until(check, done, every, within, clock=None):
    """The first value done accepts, or the last one once within seconds have passed; checks before it first sleeps."""
    clock = clock or SYSTEM
    began = clock.monotonic()
    while True:
        value = check()
        waited = clock.monotonic() - began
        if done(value):
            return Waited(value, waited, True)
        if waited >= within:
            return Waited(value, waited, False)
        clock.sleep(min(every, within - waited))
