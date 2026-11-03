"""One rails run of energy.py and preflight.py over fake traces, for the byte comparison with the recorded output."""
import json, pathlib, sys, types

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import energy, preflight  # noqa: E402

FIXTURES = pathlib.Path(__file__).parent / "fixtures"
RAILS = {"power.a": [(t, 2.0 * t) for t in range(1000, 9000, 100)], "power.b": [(t, 0.5 * t) for t in range(1000, 9000, 100)]}


class FakeTrace:

    def __init__(self, path):
        self.loaded = pathlib.Path(path).name == "busy.pftrace"

    def timed_phases(self):
        return [{"start": 900, "end": 5000, "runs": [(0, 1000, 3000), (1, 3000, 5000)], "sleeps": []}]

    def boot_minus_monotonic(self):
        return 500

    def markers(self):
        return {"d1": (2000, 7000)}

    def rails(self):
        return {name: [(t, v * 3 if self.loaded else v) for t, v in samples] for name, samples in RAILS.items()}

    def close(self):
        pass


def install_fake_trace(monkeypatch):
    monkeypatch.setitem(sys.modules, "rails.trace", types.SimpleNamespace(Trace=FakeTrace))


def inputs(folder):
    (folder / "data.json").write_text(json.dumps({"benchmarks": [
        {"name": "measure[m1]", "repeatIterations": 40, "metrics": {"timeNs": {"runs": [1, 2, 3]}},
         "profilerOutputs": [{"type": "PerfettoTrace", "filename": "m1.trace"}]},
        {"name": "measure[m2]", "repeatIterations": 5, "metrics": {"timeNs": {"runs": [9]}},
         "profilerOutputs": [{"type": "PerfettoTrace", "filename": "m2.trace"}]}]}))
    (folder / "prepared.yaml").write_text("run: {harness: {energy: {capture: measured}}}\n"
                                          "cases: [{id: m1}, {id: m2}, {id: d1, harness: {energy: {capture: dry}}}]\n")
    (folder / "m1.trace").write_text("")
    (folder / "m2.trace").write_text("")
    (folder / "dry.pftrace").write_text("")
    (folder / "calls.yaml").write_text("d1: 77\n")
    (folder / "energy.yaml").write_text("schemaVersion: 1\nrailsPresent: true\nrailsResponsive: true\nidleMicrojoules: 3000.0\n"
                                        "busyMicrojoules: 9000.0\nwindowSeconds: 3.0\nacceptUnresponsive: false\n")


def arguments(folder, out):
    inputs(folder)
    return ["--capability", str(folder / "energy.yaml"), "-o", str(out), "--prepared", str(folder / "prepared.yaml"),
            "--benchmark-data", str(folder / "data.json"), "--traces", str(folder),
            "--dry-trace", str(folder / "dry.pftrace"), "--dry-calls", str(folder / "calls.yaml")]


def run_energy(folder):
    out = folder / "energy.json"
    energy.main(arguments(folder, out))
    return out.read_text()


def run_preflight(folder):
    out = folder / "preflight.yaml"
    preflight.main([str(folder / "idle.pftrace"), str(folder / "busy.pftrace"), "3", str(out)])
    return out.read_text()
