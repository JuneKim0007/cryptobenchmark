import pathlib
import sys

import pytest
import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import interop_stage  # noqa: E402
from device import FILES, DeviceError  # noqa: E402

RESULT = {"schemaVersion": 1, "pairs": [
    {"id": 1, "group": "oaep", "result": "fail", "reason": "aToB: BadPaddingException"},
    {"id": 2, "group": "gcm", "result": "pass", "reason": ""}]}


class FakeDevice:

    def __init__(self, output):
        self.output, self.calls = output, []

    def shell(self, command):
        self.calls.append(("shell", command))

    def run(self, *arguments):
        self.calls.append(("run", *arguments))

    def instrument(self, test_class):
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


def test_the_device_check_pushes_runs_and_pulls(tmp_path):
    device = FakeDevice("OK (1 test)\n")
    interop_stage.on_device(device, "e.yaml", "p.yaml", "t.yaml", "interop_plan.yaml", tmp_path / "interop.yaml")
    assert device.calls[1] == ("run", "push", "e.yaml", "p.yaml", "t.yaml", "interop_plan.yaml", f"{FILES}/")
    assert device.calls[2:] == [("instrument", "InteropCheck"), ("pull", f"{FILES}/interop.yaml", str(tmp_path / "interop.yaml"))]


def test_a_failed_device_check_is_an_error():
    with pytest.raises(DeviceError, match="InteropCheck failed"):
        interop_stage.on_device(FakeDevice("INSTRUMENTATION_FAILED: x\n"), "e", "p", "t", "plan", pathlib.Path("out"))


def test_the_summary_names_every_pair_that_did_not_pass(tmp_path, capsys):
    out = tmp_path / "interop.yaml"
    out.write_text(yaml.safe_dump(RESULT))
    interop_stage.summary(out)
    assert capsys.readouterr().out.splitlines() == ["interop:   1 oaep fail: aToB: BadPaddingException",
                                                    "interop:   2 pairs, 1 fail, 1 pass"]
