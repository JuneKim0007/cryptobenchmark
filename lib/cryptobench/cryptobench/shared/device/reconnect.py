"""A device whose adb transport is lost mid-run: a bounded wait polling adb get-state, then the step again; past the bound the run stops."""
from cryptobench.shared.device.adb import DeviceLost
from cryptobench.shared.errors.coded import Coded
from cryptobench.shared.wait.until import until

WAIT_MINUTES, POLL_SECONDS = 60, 10   # the defaults of pipeline.py --reconnect-wait-minutes and --reconnect-poll-seconds
SECONDS_PER_MINUTE = 60


class DeviceGone(Coded):
    """Ends the run; never a DeviceLost, which the session waits out."""


def say(line):
    print(f"device:    {line}")


class Reconnect:
    """Once gone, every later loss stops at once, so closing hooks never wait the bound again."""

    def __init__(self, device, wait_seconds, poll_seconds):
        self.device, self.wait, self.poll, self.gone = device, wait_seconds, poll_seconds, None

    @classmethod
    def of(cls, device, options):
        minutes = WAIT_MINUTES if options.reconnect_wait_minutes is None else options.reconnect_wait_minutes
        poll = POLL_SECONDS if options.reconnect_poll_seconds is None else options.reconnect_poll_seconds
        return cls(device, minutes * SECONDS_PER_MINUTE, poll)

    def line(self):
        return f"device:    a lost adb transport is waited for up to {self.wait // SECONDS_PER_MINUTE} min, adb get-state every {self.poll} s"

    def back(self, lost, step):
        """Returns once adb get-state says device again; DeviceGone past the bound."""
        if self.gone:
            raise DeviceGone(self.gone) from lost
        say(f"{lost}; waiting up to {self.wait} s for adb get-state to say device")
        waited = until(self.device.state, lambda state: state == "device", self.poll, self.wait)
        if waited.met:
            say(f"back after {waited.seconds:.0f} s; {step} again")
            return
        self.gone = f"{lost}; not back after {waited.seconds:.0f} s (adb get-state: {waited.value or 'no answer'}); run stopped"
        raise DeviceGone(self.gone) from lost

    def retried(self, step, label):
        while True:
            try:
                return step()
            except DeviceLost as lost:
                self.back(lost, label)


class Off:
    """No wait: a lost device ends the step as any device error does."""

    def back(self, lost, _step):
        raise lost

    def retried(self, step, _label):
        return step()
