"""A fake clock installed as until's system clock: sleeping advances now and calls on_sleep."""
from cryptobench.shared.wait import until


class FakeClock:
    def __init__(self, monkeypatch, on_sleep=lambda _seconds: None):
        self.now, self.slept, self.on_sleep = 0.0, [], on_sleep
        monkeypatch.setattr(until, "SYSTEM", self)

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.slept.append(seconds)
        self.now += seconds
        self.on_sleep(seconds)
