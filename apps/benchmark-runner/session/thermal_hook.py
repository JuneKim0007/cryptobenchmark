"""Temperature around every case and process of a session, into each process's thermal.json, and one line per pass; never a failed case."""
import json

from device import thermal
from session.measure import Hooks
from cryptobench import paths

SCHEMA_VERSION = 1


def record(start, end, scope=None):
    """benchmark.json's thermal shape; why a reading is missing, cached or the process's goes in note, never in that shape."""
    entry = {"start": start.sensors, "end": end.sensors, "startStatus": start.status, "endStatus": end.status}
    notes = [r for r in (start.reason, end.reason) if r][:1]
    notes += ["source: cached"] if "cached" in (start.source, end.source) else []
    notes += [f"scope: {scope}"] if scope else []
    if notes:
        entry["note"] = "; ".join(notes)
    return entry


def sleeps(data):
    if not data.is_file():
        return {}
    benchmarks = json.loads(data.read_text()).get("benchmarks") or []
    return {b["name"][b["name"].index("[") + 1:-1] if "[" in b["name"] else b["name"]: b.get("thermalThrottleSleepSeconds") or 0 for b in benchmarks}


class Thermal(Hooks):
    """With one process for every case there is no case boundary: each case gets the process's reading, scope run."""

    def __init__(self, device, label):
        self.device, self.label = device, label
        self.process_start, self.case_start, self.cases, self.paused = None, None, {}, {}

    def before_session(self):
        self.cases, self.paused = {}, {}

    def before_process(self, _process):
        self.process_start = thermal.read(self.device)

    def before_case(self, _process, _case):
        self.case_start = thermal.read(self.device)

    def after_case(self, process, case, _failure):
        self.cases.setdefault(process.repetition, {})[case] = record(self.case_start, thermal.read(self.device))

    def after_process(self, process):
        end = thermal.read(self.device)
        cases = self.cases.setdefault(process.repetition, {})
        paused = sleeps(process.data)
        for case in paused:
            cases.setdefault(case, record(self.process_start, end, scope="run"))
        self.paused[process.repetition] = paused
        document = {"schemaVersion": SCHEMA_VERSION, "process": record(self.process_start, end), "cases": cases}
        paths.Measurement(process.into).thermal.write_text(json.dumps(document, indent=1))

    def after_session(self, _processes):
        print(summary(self.label, [c for cases in self.cases.values() for c in cases.values()],
                      [s for paused in self.paused.values() for s in paused.values()]))


def hottest(records):
    starts = [max(r["start"].values()) for r in records if r["start"]]
    ends = [max(r["end"].values()) for r in records if r["end"]]
    if starts and ends:
        return f"hottest {max(starts):.1f} C at a case start, {max(ends):.1f} C at an end"
    return "temperature unavailable: " + next((r["note"] for r in records if r.get("note")), "no case measured")


def summary(label, records, paused):
    throttled = sum(1 for r in records if (r["endStatus"] or 0) > 0)
    heat = hottest(records)
    return (f"thermal:   {label}: {heat}; {sum(1 for s in paused if s)} pauses, {sum(paused)} s paused; "
            f"{throttled} case{'' if throttled == 1 else 's'} ended throttled (status > 0)")
