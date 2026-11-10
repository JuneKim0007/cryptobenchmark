"""Whole stdout of fake-phone device runs against golden/flow_*.txt, temporary paths and wall-clock times normalised; UPDATE_GOLDEN=1 rewrites them."""
import os, pathlib, re, types

import pytest

import test_device_benchmark_flow as flow
from test_device_benchmark_flow import DUMP, MEASURED, measured
from test_thermal_gate import CASE, Heat

GOLDEN = pathlib.Path(__file__).with_name("golden")
TIMES = ((re.compile(r"^(took:\s+.* in )\d+\.\ds$", re.M), r"\1<s>s"), (re.compile(r"\d+m \d\ds on the device"), "<m s> on the device"),
         (re.compile(r"^(warm-up: .* in )\d+s,", re.M), r"\1<s>s,"))


def normalised(out, tmp_path):
    out = out.replace(str(tmp_path), "<tmp>")
    for pattern, replacement in TIMES:
        out = pattern.sub(replacement, out)
    return out


def suppressed(monkeypatch):
    monkeypatch.setattr(flow, "OPTIONS", types.SimpleNamespace(**{**vars(flow.OPTIONS), "suppress_errors": "EMULATOR"}))


FLOWS = {
    "case_crash_retried": lambda tmp_path, monkeypatch: measured(tmp_path, monkeypatch, {"isolation": "case", "launchRetries": 1},
                                                                 cases=("a", "crash", "b"), crash=("crash",)),
    "energy_and_timing_passes": lambda tmp_path, monkeypatch: measured(tmp_path, monkeypatch, MEASURED),
    "gate_discard": lambda tmp_path, monkeypatch: (Heat(monkeypatch, start=35.7, rise=0.4, cooling=0.05), measured(tmp_path, monkeypatch, CASE)),
    "run_isolation_warnings": lambda tmp_path, monkeypatch: (suppressed(monkeypatch), measured(
        tmp_path, monkeypatch, {"isolation": "run", "processRepetitions": 2, "warmup": {"iterations": 5, "jobs": [{"provider": "X", "type": "T", "name": "z"}]},
                                "passes": {"energy": {"samples": 2}, "timing": {"samples": 2}}}, thermal=DUMP)),
    "warmup_failed_cooldown": lambda tmp_path, monkeypatch: (monkeypatch.setattr(flow.cooldown_hook.time, "sleep", lambda _s: None), measured(
        tmp_path, monkeypatch, {"isolation": "case", "caseCooldownSeconds": 4, "warmup": {"iterations": 5, "jobs": []}}, crash=("a,b",), thermal=DUMP)),
}


@pytest.mark.parametrize("name", FLOWS)
def test_the_whole_stdout_of_a_fake_phone_run(name, tmp_path, monkeypatch, capsys):
    FLOWS[name](tmp_path, monkeypatch)
    out = normalised(capsys.readouterr().out, tmp_path)
    golden = GOLDEN / f"flow_{name}.txt"
    if os.environ.get("UPDATE_GOLDEN"):
        golden.write_text(out)
    assert out == golden.read_text()
