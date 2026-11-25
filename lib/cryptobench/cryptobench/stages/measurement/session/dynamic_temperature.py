"""The thermal gate's facade, one session per pass and scope: the launch loop asks it what to do; it reads the phone and applies the equations, always in this order:
settings -> margin -> start limit -> hold -> run -> verdict -> next margin -> record."""
import dataclasses, math

from cryptobench.stages.measurement import thermal
from cryptobench.shared.log.warn import warn
from cryptobench.stages.measurement.session.gate_history import GateHistory
from cryptobench.stages.measurement import start_margin as eq
from cryptobench.shared.errors.coded import Coded
from cryptobench.shared.errors.glossary import STOP
from cryptobench.shared.errors.policy import resolve
from cryptobench.shared.settings.effective_view import RUN_GATE, GateView, gate_scopes
from cryptobench.shared.wait.until import until

SECONDS_PER_MINUTE = 60
UNREADABLE = "unreadable"


class Terminated(Coded):
    """Ends the whole benchmark; never a DeviceError, which the warm-up and the energy steps catch."""


def say(line):
    print(f"gate:      {line}")


@dataclasses.dataclass(frozen=True)
class Settings:
    kept: float
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
        return cls(gate.kept, gate.poll_seconds, gate.terminate_seconds, gate.discard_limit,
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
        """read, then thermal.poll every readRetrySeconds while unreadable, readRetries times at most."""
        reads = [read, *[thermal.poll] * self.settings.read_retries]
        return until(lambda: reads.pop(0)(self.device), lambda reading: reading.skin or not reads,
                     self.settings.read_retry_seconds, math.inf).value

    def cool(self, reading):
        """An unreadable reading is never cool."""
        return bool(reading.skin) and reading.skin[1] <= self.limit() and (reading.status or 0) <= 0

    def hold(self, case):
        """True once the phone may start this run; False when its temperature cannot be read; Terminated past pollTerminateSeconds."""
        self.started = None
        reading, limit = self.readable(thermal.read), self.limit()
        if not reading.skin:
            warn(f"temperature_unreadable: {case}: {reading.reason or 'no skin sensor in this reading'}", self.problems)
            return False
        if self.cool(reading):
            self.history.passed(case, limit, 0.0)
            self.started = reading
            return True
        poll = self.settings.poll
        say(f"{case}: {reading.skin[1]:.1f} C, start limit {limit:.2f} C => waiting, reading it every {poll} s")
        first, polls, per_line = [reading], [], max(1, SECONDS_PER_MINUTE // poll)

        def polled():
            if first:
                return first.pop()
            polls.append(thermal.poll(self.device))
            if len(polls) % per_line == 0 and not self.cool(polls[-1]):
                now = f"{polls[-1].skin[1]:.1f} C, waiting" if polls[-1].skin else "unreadable, not a pass, waiting"
                say(f"{case}: poll {len(polls)}: {now}")
            return polls[-1]
        waited = until(polled, self.cool, poll, self.settings.terminate)
        if not waited.met:
            raise Terminated(f"temperature_gate_timeout: {case}: {self.label}: still above {limit:.2f} C after {waited.seconds:.0f} s; benchmark stopped")
        say(f"{case}: passed at {waited.value.skin[1]:.1f} C after {waited.seconds:.0f} s")
        self.history.passed(case, limit, waited.seconds)
        return True

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
