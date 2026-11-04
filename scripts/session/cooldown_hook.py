"""Session hook: run.caseCooldownSeconds of host sleep before every measured case but a session's first; one line per pass."""
import time

from session.measure import Hooks


class Cooldown(Hooks):
    """With one process for every case the only boundary the host sees is between processes, so the sleep goes there."""

    def __init__(self, seconds, label, per_case, sleep=None):
        self.seconds, self.label, self.per_case, self.sleep = seconds, label, per_case, sleep or time.sleep
        self.started, self.gaps = False, 0

    def before_session(self):
        self.started, self.gaps = False, 0

    def before_process(self, _process):
        if not self.per_case:
            self.pause()

    def before_case(self, _process, _case):
        if self.per_case:
            self.pause()

    def pause(self):
        if self.started and self.seconds:
            self.sleep(self.seconds)
            self.gaps += 1
        self.started = True

    def after_session(self, _processes):
        if self.seconds:
            print(f"cool-down: {self.label}: {self.gaps} x {self.seconds} s = {self.gaps * self.seconds} s between {'cases' if self.per_case else 'processes'}")
