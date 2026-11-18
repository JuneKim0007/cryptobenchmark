import io
import pathlib
import sys

import pytest
import yaml

from cryptobench.pipeline.orchestrator import run as session_run
from cryptobench.pipeline.orchestrator.board import StatusBoard
from cryptobench.shared.device.probe import DeviceRow
from cryptobench.shared.errors.failures import CommandError
from cryptobench.shared.errors.input_error import InputError

FAKE = pathlib.Path(__file__).with_name("fake_worker.py")
PIXEL = DeviceRow("56301AAAA00001", "56301AAAA00001", "device", "physical", "Pixel 10", 37, "usb")
EMU = DeviceRow("emulator:cb-api33", "emulator-5554", "device", "emulator", "sdk", 33, "emulator")
SAMSUNG = DeviceRow("R58N00000001", "R58N00000001", "unauthorized", connection="usb", reason="device_unauthorized: R58N00000001 is unauthorized; unlock it")


def fake(target, config, results, passed):
    mode = "--bench" if target.transport is None else "--device"
    return [sys.executable, str(FAKE), "--config", str(config), "--results", str(results), "--per-suite", mode, *passed]


@pytest.fixture
def session(tmp_path, monkeypatch):
    monkeypatch.setattr(session_run, "POLL_SECONDS", 0.05)
    monkeypatch.setattr(session_run.session_plan.probe, "enumerate_devices", lambda _adb: [PIXEL, EMU, SAMSUNG])
    monkeypatch.setattr(session_run.session_plan.Device, "require_adb", lambda self: None)
    monkeypatch.setattr(session_run.session_plan.paths, "user_devices", lambda: tmp_path / "devices.yaml")
    monkeypatch.delenv("ANDROID_SERIAL", raising=False)
    for name in ("global.yaml", "tier1.yaml", "tier2.yaml", "fails.yaml", "sleeps.yaml", "skipped.yaml"):
        (tmp_path / name).write_text("schemaVersion: 1\nselection: {testSet: x.yaml}\nrun: {seed: 1}\n")

    def run(text):
        (tmp_path / "session.yaml").write_text("schemaVersion: 1\nname: s\n" + text)
        board = io.StringIO()
        try:
            return session_run.run_session(tmp_path / "session.yaml", tmp_path / "results", lambda: tmp_path / "global.yaml", [], fake,
                                           StatusBoard(board)), board.getvalue()
        finally:
            run.folder = tmp_path / "results/sessions/s"
    return run


def lines(path):
    return path.read_text().splitlines()


def logged(folder, word):
    return [line.split(" ", 1)[1] for line in lines(folder / "session.log") if line.split(" ", 2)[1] == word]


def test_groups_run_in_order_each_worker_with_its_serial_and_the_host_last(session):
    rows, _ = session("devices: {emulators: true}\nhost: {benchmark: true}\ndefaults: {config: global.yaml, suites: [tier1.yaml]}\n"
                      "targets:\n  emulator:cb-api33: {order: 1, suites: [tier1.yaml, tier2.yaml]}\n")
    folder = session.folder
    assert [(r.target, r.suite, r.state) for r in rows] == [("56301AAAA00001", "tier1", "finished"), ("emulator:cb-api33", "tier1", "finished"),
                                                           ("emulator:cb-api33", "tier2", "finished"), ("host", "tier1", "finished")]
    assert [line[len("start: "):].split(": ")[0] for line in logged(folder, "start:")] == ["56301AAAA00001 tier1", "emulator:cb-api33 tier1",
                                                                                 "emulator:cb-api33 tier2", "host tier1"]
    assert "serial:    emulator-5554 --device True" in lines(folder / "emulator-cb-api33/tier2.log")
    assert "serial:    - --bench True" in lines(folder / "host/tier1.log")
    generated = yaml.safe_load((folder / "emulator-cb-api33/tier2.global.yaml").read_text())
    root = pathlib.Path(folder).parents[2]
    assert generated == {"schemaVersion": 1, "layers": [str(root / "global.yaml")], "selection": {"testSet": str(root / "tier2.yaml")}}
    assert rows[0].results.endswith("/dev-56301AAAA00001/tier1")
    listed = yaml.safe_load((folder / "index.yaml").read_text())
    assert [(r["target"], r["suite"], r["state"]) for r in listed["runs"]] == [(r.target, r.suite, r.state) for r in rows] and listed["cases"] == []


def test_a_failed_or_skipped_target_never_holds_the_next_group(session):
    with pytest.raises(CommandError, match="^session_incomplete: 2 of 3 rows did not finish; see .*summary.txt"):
        session("devices: {select: listed}\nhost: {benchmark: true}\ndefaults: {config: global.yaml, suites: [tier1.yaml]}\n"
                "targets:\n  R58N00000001: {}\n  56301AAAA00001: {suites: [fails.yaml]}\n")
    folder = session.folder
    summary = lines(folder / "summary.txt")
    assert summary[0].split() == ["target", "suite", "state", "code", "results"]
    assert [line.split()[:4] for line in summary[1:]] == [["R58N00000001", "-", "skipped", "device_unauthorized"],
                                                         ["56301AAAA00001", "fails", "failed", "device_lost"], ["host", "tier1", "finished", "-"]]
    assert logged(folder, "skipped:") == ["skipped: R58N00000001: device_unauthorized: R58N00000001 is unauthorized; unlock it"]
    assert logged(folder, "failed:") == ["failed: 56301AAAA00001 fails: device_lost: adb shell: error: closed"]
    assert lines(folder / "R58N00000001/target.log")[-1].endswith("session: skipped: R58N00000001: device_unauthorized: R58N00000001 is unauthorized; unlock it")
    assert lines(folder / "56301AAAA00001/fails.log")[-1].endswith("session: failed: 56301AAAA00001 fails: device_lost: adb shell: error: closed")


def test_a_run_whose_every_case_is_a_coded_skip_is_an_all_skipped_row_and_the_session_completes(session):
    rows, _ = session("devices: {select: listed}\ndefaults: {config: global.yaml, suites: [skipped.yaml, tier1.yaml]}\ntargets: {56301AAAA00001: {}}\n")
    assert [(r.suite, r.state, r.code) for r in rows] == [("skipped", "all_skipped", "all_cases_skipped"), ("tier1", "finished", None)]
    summary = lines(session.folder / "summary.txt")
    assert summary[1].split()[:4] == ["56301AAAA00001", "skipped", "all_skipped", "all_cases_skipped"]
    assert logged(session.folder, "all_skipped:")[0].startswith("all_skipped: 56301AAAA00001 skipped: all_cases_skipped: every case of CryptoBenchmark")


def test_nothing_to_measure_still_writes_the_summary(session):
    with pytest.raises(InputError, match="^nothing_to_measure"):
        session("devices: {select: listed}\ndefaults: {config: global.yaml, suites: [tier1.yaml]}\ntargets: {R58N00000001: {}}\n")
    assert lines(session.folder / "summary.txt")[1].split()[:3] == ["R58N00000001", "-", "skipped"]


def test_an_inherited_serial_is_ignored_with_a_notice(session, monkeypatch, capsys):
    monkeypatch.setenv("ANDROID_SERIAL", "R58N00000001")
    session("devices: {select: listed}\ndefaults: {config: global.yaml, suites: [tier1.yaml]}\ntargets: {56301AAAA00001: {}}\n")
    assert "warning: android_serial_ignored: ANDROID_SERIAL is set; each device target gets its own serial" in capsys.readouterr().out
    assert "serial:    56301AAAA00001 --device True" in lines(session.folder / "56301AAAA00001/tier1.log")


def test_a_stop_reaches_the_running_worker_and_the_rest_never_start(session, monkeypatch):
    real_sleep, polls = session_run.time.sleep, []

    def sleep(seconds):
        polls.append(seconds)
        if len(polls) == 3:
            raise KeyboardInterrupt
        real_sleep(seconds)
    monkeypatch.setattr(session_run.time, "sleep", sleep)
    with pytest.raises(KeyboardInterrupt):
        session("devices: {select: listed}\nhost: {benchmark: true}\ndefaults: {config: global.yaml, suites: [sleeps.yaml]}\ntargets: {56301AAAA00001: {}}\n")
    folder = session.folder
    assert [line.split()[:4] for line in lines(folder / "summary.txt")[1:]] == [["56301AAAA00001", "sleeps", "stopped", "interrupted"],
                                                                               ["host", "sleeps", "not", "started"]]
    assert "error: interrupted: stopped by SIGTERM" in lines(folder / "56301AAAA00001/sleeps.log")


def test_the_board_prints_a_line_when_a_targets_status_changes(session):
    _, board = session("devices: {select: listed}\ndefaults: {config: global.yaml, suites: [tier1.yaml]}\ntargets: {56301AAAA00001: {}}\n")
    assert board.splitlines()[-1] == "target:    56301AAAA00001: tier1: finished"
