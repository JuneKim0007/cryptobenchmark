"""The thermal gate's facade, one session per pass and scope: the launch loop asks it what to do; it reads the phone and applies the equations, always in this order:
settings -> margin -> start limit -> hold -> run -> verdict -> next margin -> record."""
import dataclasses, time

from cryptobench.stages.measurement import thermal
from cryptobench.shared.log.warn import warn
from cryptobench.stages.measurement.session.gate_history import GateHistory
from cryptobench.stages.measurement import start_margin as eq
from cryptobench.shared.errors.coded import Coded
from cryptobench.shared.errors.glossary import STOP
from cryptobench.shared.errors.policy import resolve
from cryptobench.shared.settings.effective_view import RUN_GATE, GateView, gate_scopes

SECONDS_PER_MINUTE = 60
UNREADABLE = "unreadable"


class Terminated(Coded):
    """Ends the whole benchmark; never a DeviceError, which the warm-up and the energy steps catch."""


def say(line):
    print(f"gate:      {line}")


@dataclasses.dataclass(frozen=True)
class Settings:
    kept: float
    cooldown: int
    poll: int
    terminate: int
    discard_limit: int
    on_discard_limit: str
    read_retries: int
    read_retry_seconds: int
    rule: eq.StartMarginRule

    @classmethod
    def of(cls, document, base=RUN_GATE):
        """The gate block at base in effective.yaml (run.thermalGate or a pass's), every key :config writes read through required;
        on_discard_limit is the action its onDiscardLimit names (codes.yaml temperature_discard_limit values), any other value refused."""
        gate = GateView(document, base)
        initial = gate.initial
        rule = (eq.StartMarginRule(initial, gate.backoff, gate.maximum, gate.clean_runs, gate.recovery)
                if gate.dynamic else eq.StartMarginRule(initial, 1, initial, 1, 0))
        return cls(gate.kept, gate.cooldown_minutes * SECONDS_PER_MINUTE, gate.poll_minutes * SECONDS_PER_MINUTE,
                   gate.terminate_minutes * SECONDS_PER_MINUTE, gate.discard_limit,
                   resolve("temperature_discard_limit", gate.on_discard_limit, f"{base}.onDiscardLimit"), gate.read_retries, gate.read_retry_seconds, rule)


class Off:
    """No gate: every caller keeps the same calls."""

    discard_limit = None

    def __init__(self):
        self.history = GateHistory()

    def hold(self, _case):
        return True

    def take_start(self):
        return None

    def verdict(self, _case, _end=None):
        return eq.IGNORED


class DynamicTemperature:
    """One session's start margin, shared by every case; a pass builds its own."""

    def __init__(self, device, settings, sensors, problems, label, base=RUN_GATE):
        self.device, self.settings, self.problems, self.label = device, settings, problems, label
        self.margin, self.started = eq.first_margin(settings.rule), None
        self.history = GateHistory(label, {"sensors": list(sensors), "kept": settings.kept, "from": base})

    def limit(self):
        return eq.start_limit(self.settings.kept, self.margin)

    def readable(self, read):
        reading = read(self.device)
        for _ in range(self.settings.read_retries):
            if reading.skin:
                break
            time.sleep(self.settings.read_retry_seconds)
            reading = thermal.poll(self.device)
        return reading

    def cool_enough(self, reading):
        return reading.skin[1] <= self.limit() and (reading.status or 0) <= 0

    def hold(self, case):
        """True once the phone may start this run; False when its temperature cannot be read; Terminated past the polling limit."""
        self.started = None
        began, reading, limit = time.monotonic(), self.readable(thermal.read), self.limit()
        if not reading.skin:
            warn(f"temperature_unreadable: {case}: {reading.reason or 'no skin sensor in this reading'}", self.problems)
            return False
        if self.cool_enough(reading):
            self.history.passed(case, limit, 0.0)
            self.started = reading
            return True
        say(f"{case}: {reading.skin[1]:.1f} C, start limit {limit:.2f} C => waiting {self.settings.cooldown // SECONDS_PER_MINUTE} minutes to cool down, then polling every {self.settings.poll // SECONDS_PER_MINUTE} min")
        time.sleep(self.settings.cooldown)
        polls = 0
        while True:
            polls += 1
            reading = self.readable(thermal.poll)
            waited = time.monotonic() - began
            if reading.skin and self.cool_enough(reading):
                say(f"{case}: passed at {reading.skin[1]:.1f} C after {waited:.0f} s")
                self.history.passed(case, limit, waited)
                return True
            if waited >= self.settings.terminate:
                raise Terminated(f"temperature_gate_timeout: {case}: {self.label}: still above {limit:.2f} C after {waited:.0f} s; benchmark stopped")
            say(f"{case}: poll {polls}: {reading.skin[1]:.1f} C, waiting" if reading.skin else f"{case}: poll {polls}: unreadable, not a pass, waiting")
            time.sleep(self.settings.poll)

    def take_start(self):
        started, self.started = self.started, None
        return started

    def verdict(self, case, end=None):
        """The finished run, judged on its end reading when readable: hot widens the margin and is discarded, clean may narrow it,
        an unreadable end says nothing about heat."""
        reading = end if end is not None and end.skin else self.readable(thermal.poll)
        if not reading.skin:
            warn(f"temperature_unreadable: {case}: after the run; run discarded, moving to the next case", self.problems)
            return UNREADABLE
        outcome = eq.HOT if reading.skin[1] >= self.settings.kept else eq.CLEAN
        self.margin = eq.next_margin(self.margin, outcome, self.settings.rule)
        if outcome == eq.HOT:
            self.history.discarded(case)
            say(f"{case}: discarded, ended at {reading.skin[1]:.1f} C, at or above {self.settings.kept:.1f} C; start margin now {self.margin.celsius:.2f} C; measuring again")
        return outcome

    @property
    def discard_limit(self):
        return self.settings.discard_limit

    def discard_limit_reached(self, case):
        line = f"temperature_discard_limit: {case}: {self.settings.discard_limit} runs discarded"
        if self.settings.on_discard_limit == STOP:
            raise Terminated(line + "; benchmark stopped")
        warn(line + "; moving to the next case", self.problems)
        return f"case_failed: {line}"


@dataclasses.dataclass(frozen=True)
class Gate:
    """What the startup probe decided: each gate scope's settings; each pass and the warm-up ask it for their own session."""
    device: object
    settings: dict
    sensors: tuple
    problems: list

    def session(self, label, base=RUN_GATE):
        """base: the scope effective_view.scoped chose; a scope the run does not set is Off."""
        settings = self.settings.get(base)
        return DynamicTemperature(self.device, settings, self.sensors, self.problems, label, base) if settings else Off()


def opened(device, document, problems):
    """The one startup decision, one line per gate scope; a device that cannot report temperature still runs."""
    scopes = gate_scopes(document)
    if not scopes:
        say(f"TEMPERATURE GATE OFF: {RUN_GATE} not set")
        return Gate(device, {}, (), problems)
    capability = thermal.capability(device)
    if not capability.available:
        warn(f"TEMPERATURE SET BUT DEVICE CAN'T POLL: {capability.reason}; running without it", problems)
        return Gate(device, {}, (), problems)
    settings = {base: Settings.of(document, base) for base in scopes}
    for base, one in settings.items():
        scope = "" if base == RUN_GATE else f" for {base}"
        say(f"TEMPERATURE GATE SET{scope}: kept {one.kept:.1f} C on {', '.join(capability.sensors)}; a run starts at or below {eq.start_limit(one.kept, eq.first_margin(one.rule)):.2f} C, is discarded if it ends at or above {one.kept:.1f} C")
    return Gate(device, settings, capability.sensors, problems)
