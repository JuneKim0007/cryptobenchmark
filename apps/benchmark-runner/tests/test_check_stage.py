import pathlib
import sys
import types

import pytest
import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from stages import check  # noqa: E402
from device.adb import DeviceError  # noqa: E402
import gradle_runner  # noqa: E402

FILES = "/sdcard/plan"
OPTIONS = types.SimpleNamespace(suppress_errors="EMULATOR,UNLOCKED", stacktrace=False, stream=False)
RESULT = {"schemaVersion": 1, "summary": {"cases": 3, "outcomes": {"pass": 1, "fail": 1, "notRun": 1}, "oracles": {"knownAnswer": {"pass": 1, "fail": 1}}},
          "cases": [{"id": "a", "outcome": "pass", "oracles": {}},
                    {"id": "b", "case": {"type": "MessageDigest", "algorithm": "SHA-256"}, "outcome": "fail", "oracles": {"knownAnswer": {"verdict": "fail", "reason": "output_differs"}}},
                    {"id": "c", "outcome": "notRun", "reason": "c: dry_run_failed"}]}


class FakeDevice:

    def __init__(self, output):
        self.output, self.calls, self.files = output, [], FILES

    def clear_outputs(self, names):
        self.calls.append(("clear", *names))

    def push_plan(self, *files):
        self.calls.append(("push", *map(str, files)))

    def instrument(self, test_class, *arguments):
        self.calls.append(("instrument", test_class, *arguments))
        return self.output

    def pull(self, remote, local):
        self.calls.append(("pull", remote, str(local)))

    def pull_plan(self, into):
        self.calls.append(("pull_plan", str(into)))


def test_the_device_check_runs_every_case_in_one_dry_run_process_and_pulls_its_record(tmp_path):
    device = FakeDevice("OK (12 tests)\n")
    check.on_device(device, OPTIONS, "e.yaml", "p.yaml", "t.yaml", "k.yaml", tmp_path)
    assert device.calls[1] == ("push", "e.yaml", str(pathlib.Path("e.yaml").with_name("guide.yaml")), "p.yaml", "t.yaml", "k.yaml")
    test_class, *arguments = device.calls[2][1:]
    assert test_class == "EndToEndCheck"
    assert " ".join(check.DRY_RUN) in " ".join(arguments) and "EMULATOR,UNLOCKED" in arguments
    assert device.calls[3] == ("pull", f"{FILES}/check.yaml", str(tmp_path / "check.yaml"))


def test_a_failed_device_check_is_an_error(tmp_path):
    with pytest.raises(DeviceError, match="EndToEndCheck failed"):
        check.on_device(FakeDevice("INSTRUMENTATION_FAILED: x\n"), OPTIONS, "e", "p", "t", "k", tmp_path)


def test_the_host_check_builds_the_cli_with_the_bundled_providers(tmp_path, monkeypatch):
    effective = tmp_path / "effective.yaml"
    effective.write_text(yaml.safe_dump({"bundledProviders": [{"artifact": "g:n:1", "create": "a.B"}]}))
    seen = {}
    monkeypatch.setattr(gradle_runner, "run", lambda arguments, *_a, **options: seen.update(options, arguments=arguments))
    check.on_host(OPTIONS, effective, "p.yaml", "t.yaml", "k.yaml", tmp_path)
    assert seen["main_class"] == "CheckKt" and seen["properties"] == ["-PbundledArtifacts=g:n:1"]
    assert "k.yaml" in seen["arguments"]


def test_the_summary_prints_the_counts_and_each_failure_and_counts_the_failed(tmp_path, capsys):
    result = tmp_path / "check.yaml"
    result.write_text(yaml.safe_dump(RESULT, sort_keys=False))
    assert check.summary(result) == 1
    out = capsys.readouterr().out
    assert "1 pass, 1 fail, 1 notRun of 3 cases" in out and "knownAnswer: 1 pass, 1 fail" in out
    assert "fail b: knownAnswer: output_differs" in out


def test_a_build_property_reaches_the_gradle_command():
    assert "-Pa=b" in gradle_runner._command("x", "CheckKt", ["-Pa=b"])
