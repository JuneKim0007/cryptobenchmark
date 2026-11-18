"""Session hook: run.caseCooldownSeconds of host sleep before every measured case but a session's first; one line per pass."""
import time

from cryptobench.stages.measurement.session.measure import Hooks


class Cooldown(Hooks):

    def __init__(self, seconds, label, sleep=None):
        self.seconds, self.label, self.sleep = seconds, label, sleep or time.sleep
        self.started, self.gaps = False, 0

    def before_session(self):
        self.started, self.gaps = False, 0

    def before_case(self, _process, _case):
        if self.started and self.seconds:
            self.sleep(self.seconds)
            self.gaps += 1
        self.started = True

    def after_session(self, _processes):
        if self.seconds:
            print(f"cool-down: {self.label}: {self.gaps} x {self.seconds} s = {self.gaps * self.seconds} s between cases")
