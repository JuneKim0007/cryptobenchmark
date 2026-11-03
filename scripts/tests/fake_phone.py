"""The phone over adb, faked: an instrumentation per process, one log line per device step, and the host tools' files."""
import contextlib, json, pathlib, sys, types

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import case_isolation  # noqa: E402
import device as device_module  # noqa: E402
import gradle_runner  # noqa: E402
import timeouts  # noqa: E402

OK = types.SimpleNamespace(returncode=0, stdout="", stderr="")
MISSING = types.SimpleNamespace(returncode=1, stdout="", stderr="not found")
CRASHED = "INSTRUMENTATION_RESULT: shortMsg=Process crashed.\nINSTRUMENTATION_CODE: 0\n"


def jetpack_case(case, sleep=0):
    return {"name": f"measure[{case}]", "repeatIterations": 10, "thermalThrottleSleepSeconds": sleep, "totalRunTimeNs": 10**9,
            "metrics": {"timeNs": {"minimum": 1.0, "maximum": 1.0, "median": 1.0, "coefficientOfVariation": 0.0, "runs": [1.0]}}}


class Phone(device_module.Device):

    def __init__(self, folder, cases=("a", "b"), crash=(), hang=(), thermal=None):
        super().__init__(pathlib.Path(folder), False, False)
        self.files, self.media, self.data = "/plan", "/media", "/media/data.json"
        self.cases, self.crash, self.hang = list(cases), set(crash), set(hang)
        self.written, self.log, self.ran, self.arguments, self.converted = [], [], [], [], []
        self.thermal, self.notices = thermal, []

    def run(self, *arguments, check=True):
        if arguments[0] == "pull":
            return self.pulled(arguments[1], arguments[2], check)
        if arguments[0] == "shell":
            self.shell(arguments[1])
            return OK
        self.log.append(f"adb {arguments[0]} " + " ".join(pathlib.Path(a).name for a in arguments[1:-1]))
        return OK

    def pulled(self, remote, local, check):
        if remote == self.data and self.written:
            self.log.append("pull data")
            pathlib.Path(local).write_text(json.dumps({"context": {"build": {"model": "fake"}}, "benchmarks": [jetpack_case(c) for c in self.written]}))
            return OK
        if remote.endswith(device_module.CPU_PINS):
            self.log.append("pull pins")
            return MISSING
        if check:
            raise device_module.DeviceError(f"adb pull {remote}: not found")
        return MISSING

    def pull(self, remote, local):
        if remote != self.data:
            self.log.append(f"pull {pathlib.Path(remote).name}")
        if remote.endswith("prepared.yaml"):
            pathlib.Path(local).write_text("cases:\n" + "".join(f"- {{id: {c}, type: T, algorithm: {c}, provider: P}}\n" for c in self.cases))
        elif remote.endswith("skipped.yaml"):
            pathlib.Path(local).write_text("skipped: []\n")
        elif remote.endswith(device_module.SCOPED_INTEROP):
            pathlib.Path(local).write_text("{}\n")
        elif remote == self.data:
            self.pulled(remote, local, True)

    def shell(self, command):
        if command.startswith("for c in /sys"):
            self.log.append("clocks")
        elif command.startswith("cmd package compile"):
            self.log.append("compile " + command.split()[-1].rsplit(".", 1)[-1])
            return "Success"
        elif command.startswith("dumpsys thermalservice"):
            self.log.append("thermal")
            if self.thermal is None:
                raise device_module.DeviceError("adb shell dumpsys thermalservice: Can't find service")
            return self.thermal
        elif command.startswith(f"rm -f {self.data}"):
            self.written = []
        elif command.startswith("rm -f"):
            self.written = []
            self.log.append("clear")
        elif command.startswith("am force-stop"):
            self.log.append("force-stop")
        return ""

    def instrument(self, test_class, *arguments, step="instrument"):
        if "log" in arguments:
            self.log.append(f"list {test_class}")
            return "".join(f"INSTRUMENTATION_STATUS: test=measure[{c}]\n" for c in self.cases) + "OK (0 tests)\n"
        named = arguments[arguments.index(case_isolation.CASE_ARGUMENT) + 1] if case_isolation.CASE_ARGUMENT in arguments else None
        self.log.append(f"instrument {test_class}" + (f" {named}" if named else ""))
        if test_class == "ScopedInterop":
            return "OK (1 test)\n"
        self.arguments.append(arguments)
        wanted = named.split(",") if named else list(self.cases)
        self.ran.append((test_class, named))
        if named in self.crash:
            return CRASHED
        if named in self.hang:
            raise timeouts.expired(step, ["adb", "shell", "am", "instrument"])
        self.written = wanted
        return "OK (1 test)\n" if len(wanted) == 1 else f"OK ({len(wanted)} tests)\n"


class Energy:
    """A rails source with no rails: logs the window and joules, writes nothing."""

    def __init__(self, phone):
        self.phone = phone

    def preflight(self, _session, discovery, _accept):
        self.phone.log.append("preflight")
        capability = discovery / "energy.yaml"
        capability.write_text("railsResponsive: true\n")
        return capability

    def window(self, _folder):
        @contextlib.contextmanager
        def around():
            self.phone.log.append("window open")
            yield
            self.phone.log.append("window close")
        return around()

    def joules(self, *paths):
        self.phone.log.append("joules")
        if paths and isinstance(paths[-1], pathlib.Path):
            paths[-1].write_text("{}")


def fake_convert(phone, arguments, words, notices):
    phone.log.append("convert")
    if notices is not None:
        notices.extend(phone.notices)
    data, into = pathlib.Path(words[0]), pathlib.Path(words[2])
    names = [b["name"][8:-1] for b in json.loads(data.read_text())["benchmarks"]]
    into.mkdir(parents=True, exist_ok=True)
    phone.converted.append(arguments)
    metric = {"ALLOCATION": "allocationCount"}.get(arguments.split("--metrics=TIME,")[-1].split()[0], None) if "--metrics=TIME," in arguments else None
    extra = {"energyJ": {"runs": [2.0]}} if len(words) > 3 and words[3].endswith("energy.json") else {metric: {"runs": [3.0]}} if metric else {}
    (into / "benchmark.json").write_text(json.dumps({"runtime": {}, "cases": [{"id": n, "metrics": {"timeNs": {"runs": [1.0]}, **extra}} for n in names]}))


def fake_merge_passes(phone, words):
    phone.log.append("merge passes")
    out, base = pathlib.Path(words[0]), json.loads(pathlib.Path(words[1]).read_text())
    for owned in words[2:]:
        key, path = owned.split("=", 1)
        cases = {c["id"]: c for c in json.loads(pathlib.Path(path).read_text())["cases"]}
        for case in base["cases"]:
            case["metrics"].pop(key, None)
            case["metrics"].update({key: cases[case["id"]]["metrics"][key]} if key in cases.get(case["id"], {}).get("metrics", {}) else {})
    out.mkdir(parents=True, exist_ok=True)
    (out / "benchmark.json").write_text(json.dumps(base))


def fake_merge_runs(phone, words):
    phone.log.append("merge")
    out, cases = pathlib.Path(words[0]), {}
    for path in words[1:]:
        for case in json.loads(pathlib.Path(path).read_text())["cases"]:
            kept = cases.setdefault(case["id"], {"id": case["id"], "metrics": {}})
            for metric, block in case["metrics"].items():
                kept["metrics"].setdefault(metric, {"runs": []})["runs"] += block["runs"]
    out.mkdir(parents=True, exist_ok=True)
    (out / "benchmark.json").write_text(json.dumps({"runtime": {}, "cases": list(cases.values())}))


def fake_tools(monkeypatch, phone):
    """ConvertKt, MergePassesKt and MergeRunsKt: the same files as the real tools, from the fake data."""
    def run(_project, arguments, _stacktrace, _stream=False, main_class=None, notices=None):
        words = arguments.split()
        if main_class == "ConvertKt":
            fake_convert(phone, arguments, words, notices)
        elif main_class == "MergePassesKt":
            fake_merge_passes(phone, words)
        elif main_class == "MergeRunsKt":
            fake_merge_runs(phone, words)
        return []
    monkeypatch.setattr(gradle_runner, "run", run)
