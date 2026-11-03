"""isolation: case over a fake instrumentation: one case aborts its process, the others still produce results."""
import json, pathlib, sys, types

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import case_isolation  # noqa: E402
import device as device_module  # noqa: E402
import timeouts  # noqa: E402

LISTING = "".join(f"INSTRUMENTATION_STATUS: test=measure[{case}]\nINSTRUMENTATION_STATUS_CODE: 1\n" for case in ("a", "crash", "b", "hang"))
CRASHED = "INSTRUMENTATION_RESULT: shortMsg=Process crashed.\nINSTRUMENTATION_CODE: 0\n"


class FakeDevice(device_module.Device):
    """The phone: a case's own process writes benchmarkData.json with that case only; `crash` aborts, `hang` never ends."""

    def __init__(self, folder):
        super().__init__(folder, False, False)
        self.files, self.media, self.data = "/plan", "/media", "/media/data.json"
        self.written, self.calls = None, []

    def run(self, *arguments, check=True):
        self.calls.append(arguments[:2])
        if arguments[0] == "pull" and arguments[1] == self.data and self.written:
            pathlib.Path(arguments[2]).write_text(json.dumps(self.written))
            return types.SimpleNamespace(returncode=0, stdout="", stderr="")
        if arguments[0] == "pull" and check:
            raise device_module.DeviceError(f"adb pull {arguments[1]}: not found")
        return types.SimpleNamespace(returncode=1 if arguments[0] == "pull" else 0, stdout="", stderr="")

    def pull(self, remote, local):
        self.calls.append(("pull", remote))

    def shell(self, command):
        if command.startswith(f"rm -f {self.data}"):
            self.written = None
        return ""

    def instrument(self, test_class, *arguments, step="instrument"):
        if "log" in arguments:
            return LISTING + "OK (0 tests)\n"
        case = arguments[arguments.index(case_isolation.CASE_ARGUMENT) + 1]
        if case == "crash":
            return CRASHED
        if case == "hang":
            raise timeouts.expired(step, ["adb", "shell", "am", "instrument"])
        self.written = {"context": {"build": {"model": "fake"}}, "benchmarks": [{"name": f"measure[{case}]"}]}
        return "OK (1 test)\n"


def test_a_case_that_kills_its_process_loses_only_itself(tmp_path, capsys):
    phone = FakeDevice(tmp_path)
    data, preparation = tmp_path / "benchmark/benchmarkData.json", tmp_path / "preparation"
    failures = phone.measure("", ["TIME"], data, preparation, "case")
    assert [b["name"] for b in json.loads(data.read_text())["benchmarks"]] == ["measure[a]", "measure[b]"]
    assert failures == ["case_failed: crash: INSTRUMENTATION_RESULT: shortMsg=Process crashed.",
                        "case_failed: hang: timeout: case ran past 3600 s: adb shell am instrument"]
    assert ("shell", f"am force-stop {device_module.PACKAGE}") in phone.calls
    out = capsys.readouterr().out
    assert "measure:   one process per case (4 cases, isolation: case)" in out and out.count("case_failed: ") == 2
    assert not list(data.parent.glob(".*.json"))


def test_every_case_failing_is_the_runs_failure(tmp_path):
    phone = FakeDevice(tmp_path)
    phone.instrument = lambda _class, *arguments, step="instrument": LISTING if "log" in arguments else CRASHED
    with pytest.raises(device_module.DeviceError, match="CryptoBenchmark failed on the device for every case:"):
        phone.measure("", ["TIME"], tmp_path / "b/data.json", tmp_path / "p", "case")


def test_isolation_run_keeps_one_process_for_every_case(tmp_path, capsys):
    phone = FakeDevice(tmp_path)
    phone.instrument = lambda _class, *arguments, step="instrument": "OK (4 tests)\n"
    assert phone.measure("", ["TIME"], tmp_path / "b/data.json", tmp_path / "p", "run") == []
    assert "measure:   one process for every case (isolation: run)" in capsys.readouterr().out


def test_the_listing_is_the_planned_cases_in_order():
    assert case_isolation.listed(LISTING + LISTING) == ["a", "crash", "b", "hang"]


def test_one_data_file_from_many_processes_keeps_the_first_context():
    documents = [{"context": {"n": 1}, "benchmarks": [{"name": "x"}]}, {"context": {"n": 2}, "benchmarks": [{"name": "y"}]}]
    assert case_isolation.merged(documents) == {"context": {"n": 1}, "benchmarks": [{"name": "x"}, {"name": "y"}]}
