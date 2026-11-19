import pathlib

import pytest
import yaml

from cryptobench.stages.verification import interop_oracle as interop_stage  # noqa: E402
from cryptobench.shared.device.adb import Device, DeviceError  # noqa: E402
from cryptobench.shared.device.reconnect import Off  # noqa: E402

FILES = "/sdcard/plan"

RESULT = {"schemaVersion": 1, "pairs": [
    {"id": 1, "group": "oaep", "result": "fail", "reason": "aToB: BadPaddingException"},
    {"id": 2, "group": "gcm", "result": "pass", "reason": ""}]}


class FakeDevice(Device):

    def __init__(self, output):
        self.output, self.calls, self.files = output, [], FILES

    def shell(self, command):
        self.calls.append(("shell", command))
        return "Success"

    def run(self, *arguments):
        self.calls.append(("run", *arguments))

    def instrument(self, test_class, step="instrument"):
        self.calls.append(("instrument", test_class))
        return self.output

    def pull(self, remote, local):
        self.calls.append(("pull", remote, str(local)))


def test_the_plan_is_staged_under_its_contract_name_and_a_stale_result_removed(tmp_path):
    source = tmp_path / "mine.yaml"
    source.write_text("schemaVersion: 1\npairs: []\n")
    into = tmp_path / "results/interop"
    into.mkdir(parents=True)
    (into / "interop.yaml").write_text("stale")
    staged = interop_stage.stage_plan(source, into)
    assert staged == into / "interop_plan.yaml" and staged.read_text() == source.read_text()
    assert not (into / "interop.yaml").exists()
    assert interop_stage.stage_plan(staged, into) == staged


def test_the_device_check_pushes_compiles_runs_and_pulls(tmp_path):
    device = FakeDevice("OK (1 test)\n")
    interop_stage.on_device(device, Off(), "e.yaml", "p.yaml", "t.yaml", "interop_plan.yaml", tmp_path / "interop.yaml")
    assert device.calls[0] == ("run", "push", "e.yaml", "p.yaml", "t.yaml", "interop_plan.yaml", f"{FILES}/")
    assert [c[1].split()[:3] for c in device.calls[1:3]] == [["cmd", "package", "compile"]] * 2
    assert device.calls[3:] == [("shell", f"rm -f {FILES}/interop.yaml"), ("instrument", "InteropCheck"),
                                ("pull", f"{FILES}/interop.yaml", str(tmp_path / "interop.yaml"))]


def test_a_failed_device_check_is_an_error():
    with pytest.raises(DeviceError, match="InteropCheck failed"):
        interop_stage.on_device(FakeDevice("INSTRUMENTATION_FAILED: x\n"), Off(), "e", "p", "t", "plan", pathlib.Path("out"))


def test_the_summary_names_every_pair_that_did_not_pass(tmp_path, capsys):
    out = tmp_path / "interop.yaml"
    out.write_text(yaml.safe_dump(RESULT))
    interop_stage.summary(out)
    out = capsys.readouterr().out
    assert "1 oaep fail" in out and "gcm" not in out


def test_the_host_interop_builds_the_cli_with_the_bundled_providers_and_names_the_effective_file(tmp_path, monkeypatch):
    from cryptobench.shared.device import gradle_runner
    effective = tmp_path / "effective.yaml"
    effective.write_text(yaml.safe_dump({"bundledProviders": [{"artifact": "g:n:1", "create": "a.B"}]}))
    seen = {}
    monkeypatch.setattr(gradle_runner, "run", lambda arguments, *_a, **options: seen.update(options, arguments=arguments))
    interop_stage.on_host(effective, "p.yaml", "t.yaml", "plan.yaml", "out.yaml", False, False)
    assert seen["main_class"] == "InteropKt" and seen["properties"] == ["-PbundledArtifacts=g:n:1"]
    assert seen["arguments"] == f"p.yaml t.yaml {effective} plan.yaml out.yaml"
