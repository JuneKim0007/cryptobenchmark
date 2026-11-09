"""run.thermalGate's facade: the launch loop asks it what to do; it reads the phone and applies the equations, always in this order:
settings -> margin -> start limit -> hold -> run -> verdict -> next margin -> record."""
import dataclasses, time

from device import thermal
from failure import warn
from cryptobench.measure import equations as eq

SECONDS_PER_MINUTE = 60
STOP = "stop"
UNREADABLE = "unreadable"


class Terminated(Exception):
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
    def of(cls, gate):
        m = gate["startMargin"]
        rule = (eq.StartMarginRule(m["initialCelsius"], m["backoffFactor"], m["maximumCelsius"], m["cleanRunsToRecover"], m["recoveryCelsius"])
                if m["dynamic"] else eq.StartMarginRule(m["initialCelsius"], 1, m["initialCelsius"], 1, 0))
        return cls(gate["temperatureKeptCelsius"], gate["cooldownMinutes"] * SECONDS_PER_MINUTE, gate["pollMinutes"] * SECONDS_PER_MINUTE,
                   gate["pollTerminateMinutes"] * SECONDS_PER_MINUTE, gate["discardLimit"], gate["onDiscardLimit"], gate["readRetries"],
                   gate["readRetrySeconds"], rule)


class Off:
    """No gate: every caller keeps the same calls."""

    discard_limit = None

    def hold(self, _case):
        return True

    def take_start(self):
        return None

    def note_end(self, _reading):
        pass

    def verdict(self, _case):
        return eq.IGNORED

    def document(self):
        return None

    def records(self):
        return {}

    def summary(self):
        return None


class DynamicTemperature:
    """One session's start margin, shared by every case; a pass builds its own."""

    def __init__(self, device, settings, sensors, problems, label):
        self.device, self.settings, self.sensors, self.problems, self.label = device, settings, sensors, problems, label
        self.margin, self.held, self.started, self.ended, self.discards = eq.first_margin(settings.rule), {}, None, None, 0
        self.limits = []

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
        began, reading, limit = time.monotonic(), self.readable(thermal.read), self.limit()
        if not reading.skin:
            warn(f"temperature_unreadable: {case}: {reading.reason or 'no skin sensor in this reading'}; moving to the next case", self.problems)
            return False
        if self.cool_enough(reading):
            self.started, _ = reading, self.note(case, limit, 0.0)
            return True
        say(f"{case}: {reading.skin[1]:.1f} C, start limit {limit:.2f} C => waiting {self.settings.cooldown // SECONDS_PER_MINUTE} minutes to cool down, then polling each minute")
        time.sleep(self.settings.cooldown)
        polls = 0
        while True:
            polls += 1
            reading = self.readable(thermal.poll)
            waited = time.monotonic() - began
            if reading.skin and self.cool_enough(reading):
                say(f"{case}: passed at {reading.skin[1]:.1f} C after {waited:.0f} s")
                self.note(case, limit, waited)
                return True
            if waited >= self.settings.terminate:
                raise Terminated(f"temperature_gate_timeout: {case}: {self.label}: still above {limit:.2f} C after {waited:.0f} s; benchmark stopped")
            say(f"{case}: poll {polls}: {reading.skin[1]:.1f} C, waiting" if reading.skin else f"{case}: poll {polls}: unreadable, not a pass, waiting")
            time.sleep(self.settings.poll)

    def note(self, case, limit, waited):
        self.limits.append(limit)
        self.held[case] = {"waitedSeconds": round(waited, 1), "target": limit, "timedOut": False, "discards": self.held.get(case, {}).get("discards", 0)}

    def take_start(self):
        started, self.started = self.started, None
        return started

    def note_end(self, reading):
        self.ended = reading

    def verdict(self, case):
        """The finished run: hot widens the margin and is discarded, clean may narrow it, an unreadable end says nothing about heat."""
        reading = self.ended if self.ended is not None and self.ended.skin else self.readable(thermal.poll)
        self.ended = None
        if not reading.skin:
            warn(f"temperature_unreadable: {case}: after the run; run discarded, moving to the next case", self.problems)
            return UNREADABLE
        outcome = eq.HOT if reading.skin[1] >= self.settings.kept else eq.CLEAN
        self.margin = eq.next_margin(self.margin, outcome, self.settings.rule)
        if outcome == eq.HOT:
            self.discards += 1
            self.held[case]["discards"] += 1
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

    def document(self):
        return {"sensors": list(self.sensors), "kept": self.settings.kept}

    def records(self):
        return self.held

    def summary(self):
        waits = [r["waitedSeconds"] for r in self.held.values()]
        limit = f"start limit {min(self.limits):.2f}-{max(self.limits):.2f} C" if self.limits else "no run started"
        return f"{self.label}: {sum(1 for w in waits if w)} of {len(waits)} cases waited, {sum(waits):.0f} s; {self.discards} runs discarded; {limit}"


@dataclasses.dataclass(frozen=True)
class Gate:
    """What the startup probe decided; each pass and the warm-up ask it for their own session."""
    device: object
    settings: Settings | None
    sensors: tuple
    problems: list

    def session(self, label):
        return DynamicTemperature(self.device, self.settings, self.sensors, self.problems, label) if self.settings else Off()


def opened(device, gate, problems):
    """The one startup decision, printed once; a device that cannot report temperature still runs."""
    if gate is None:
        say("TEMPERATURE GATE OFF: run.thermalGate not set")
        return Gate(device, None, (), problems)
    capability = thermal.capability(device)
    if not capability.available:
        warn(f"TEMPERATURE SET BUT DEVICE CAN'T POLL: {capability.reason}; running without it", problems)
        return Gate(device, None, (), problems)
    settings = Settings.of(gate)
    say(f"TEMPERATURE GATE SET: kept {settings.kept:.1f} C on {', '.join(capability.sensors)}; a run starts at or below {eq.start_limit(settings.kept, eq.first_margin(settings.rule)):.2f} C, is discarded if it ends at or above {settings.kept:.1f} C")
    return Gate(device, settings, capability.sensors, problems)
