"""The surface of manafa 0.4.14's EManafa the session reads, steered by FAKE_MANAFA; no adb."""
import os, pathlib, sys, types

BOOT = 1000.0
BEHAVIOUR = dict(pair.split("=") for pair in os.environ.get("FAKE_MANAFA", "").split(",") if pair)
TESTS = pathlib.Path(__file__).resolve().parent.parent.parent


def _rails_trace():
    # a subprocess test has no perfetto: the fake traces stand in for rails.trace
    sys.path.insert(0, str(TESTS))
    from rails_run import FakeTrace
    sys.modules["rails.trace"] = types.SimpleNamespace(Trace=FakeTrace)


_rails_trace()


def _events(times):
    return types.SimpleNamespace(events=[types.SimpleNamespace(time=t) for t in times])


class EManafa:

    def __init__(self):
        print("noise on stdout from manafa")
        if BEHAVIOUR.get("init") == "fails":
            raise RuntimeError("adb: no devices\nsecond line")
        self.power_profile = "power_profile_probed.xml"
        self.boot_time = BOOT
        self.perf_events = _events([])
        self.bat_events = None
        self.unplugged = False
        self.profiler_mode = None

    def init(self):
        pass

    def start(self):
        if self.profiler_mode != "legacy":
            raise RuntimeError("the fake only knows the legacy profiler")

    def stop(self):
        if BEHAVIOUR.get("stop") == "fails":
            self.unplugged = True
            raise RuntimeError("unable to pull trace file")
        self.perf_events = _events([BOOT] + ([BOOT + float(BEHAVIOUR.get("cover", 1.0))] if BEHAVIOUR.get("cover") != "none" else []))
        self.bat_events = _events([] if BEHAVIOUR.get("battery") == "none" else [BOOT])

    def plug_back(self):
        self.unplugged = False

    def get_consumption_in_between(self, start, end):
        if BEHAVIOUR.get("consumption") == "fails":
            raise RuntimeError("no samples")
        total = 0.0 if BEHAVIOUR.get("consumption") == "zero" else (end - start) * 1000 + 0.5
        return total, {"cpu": total}, {}
