"""run.thermalGate: before each case process the host waits while the device is hotter than its idle baseline; the timed loop is untouched."""
import dataclasses, json, time

from session import thermal_hook
from device import thermal
from session.measure import Hooks

TIMEOUT = "thermal_gate_timeout"


@dataclasses.dataclass(frozen=True)
class Target:
    sensors: tuple
    baseline: float
    celsius: float
    poll: int
    timeout: int

    def document(self):
        return {"sensors": list(self.sensors), "baseline": round(self.baseline, 1), "target": round(self.celsius, 1)}


def hottest(reading, sensors):
    found = [reading.sensors[name] for name in sensors if name in (reading.sensors or {})]
    return max(found) if found else None


def start(device, gate):
    """The idle baseline, read once before the warm-up and the first case; None leaves the run ungated."""
    if gate is None:
        return None
    sensors = tuple(gate["sensors"])
    reading = thermal.read(device)
    baseline = hottest(reading, sensors)
    if baseline is None:
        why = reading.reason or f"none of {', '.join(sensors)} among the device's sensors ({', '.join(sorted(reading.sensors or {}))})"
        print(f"warning: thermal_gate_off: {why}; measuring without the gate")
        return None
    target = Target(sensors, baseline, baseline + gate["marginCelsius"], gate["pollSeconds"], gate["timeoutSeconds"])
    absent = [name for name in sensors if name not in reading.sensors]
    print(f"gate:      baseline {baseline:.1f} C, the hottest of {', '.join(n for n in sensors if n not in absent)}; "
          f"a case starts at or below {target.celsius:.1f} C and status 0" + (f"; {', '.join(absent)} absent, skipped" if absent else ""))
    return target


def wait(device, target):
    """A case ready at the first poll waited 0 s; a poll with neither a gated sensor nor a status cannot hold a case back."""
    started, held = time.monotonic(), False
    while True:
        reading = thermal.read(device)
        hot, waited = hottest(reading, target.sensors), time.monotonic() - started
        if (hot is None or hot <= target.celsius) and (reading.status or 0) <= 0:
            return (waited if held else 0.0), False, reading
        if waited >= target.timeout:
            return waited, True, reading
        time.sleep(min(target.poll, target.timeout - waited))
        held = True


class Gate(Hooks):
    """Goes after the cool-down and before the readings, so a case's start temperature is read after its wait."""

    def __init__(self, target, device, label, per_case, problems):
        self.target, self.device, self.label, self.per_case, self.problems = target, device, label, per_case, problems
        self.records, self.held = {}, []

    def before_session(self):
        self.records, self.held = {}, []

    def before_process(self, process):
        if not self.per_case:
            self.hold(process, None)

    def before_case(self, process, case):
        if self.per_case:
            self.hold(process, case)

    def hold(self, process, case):
        waited, timed_out, reading = wait(self.device, self.target)
        record = {"waitedSeconds": round(waited, 1), "target": round(self.target.celsius, 1), "timedOut": timed_out}
        self.records.setdefault(process.repetition, {})[case] = record
        self.held.append(record)
        if timed_out:
            hot = hottest(reading, self.target.sensors)
            line = (f"{TIMEOUT}: {case or f'process-{process.repetition}'}: {self.label}: started after {waited:.0f} s at "
                    f"{'unknown' if hot is None else f'{hot:.1f}'} C, status {reading.status}, target {self.target.celsius:.1f} C")
            print(f"warning: {line}")
            self.problems.append(line)

    def after_process(self, process):
        # after_* run in reverse, so thermal_hook has written thermal.json by now; the gate joins its records to that file
        path = process.into / thermal_hook.FILE
        if not path.is_file():
            return
        document, records = json.loads(path.read_text()), self.records.get(process.repetition, {})
        document["gate"] = self.target.document()
        for case, reading in document["cases"].items():
            if (record := records.get(case if self.per_case else None)) is not None:
                reading["gate"] = record
        path.write_text(json.dumps(document, indent=1))

    def after_session(self, _processes):
        waits = [record["waitedSeconds"] for record in self.held]
        held = sum(1 for record in self.held if record["waitedSeconds"] > 0 or record["timedOut"])
        timeouts = sum(1 for record in self.held if record["timedOut"])
        print(f"gate:      {self.label}: {held} of {len(waits)} {'cases' if self.per_case else 'processes'} gated, "
              f"{sum(waits):.0f} s waited, max {max(waits, default=0):.0f} s, {timeouts} timed out")
