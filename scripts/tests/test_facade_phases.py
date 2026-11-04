"""The phases over perf-repair's fake pipeline: real guide children with the dry-run gateway, no JVM, no phone, no model."""
import json
import pathlib
import subprocess
import sys

import pytest
import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from facade import phases
from facade.index import read_index
from repo import ROOT

FIXTURES = ROOT / "apps/perf-repair/tests/fixtures"
FAKE_ROOT = FIXTURES / "device"
APP = FIXTURES / "app"
DEVICE = "fake-api36-00000000"


@pytest.fixture
def index(tmp_path):
    (tmp_path / "set.yaml").write_text("schemaVersion: 1\n")
    (tmp_path / "global.yaml").write_text("schemaVersion: 1\nselection: {testSet: set.yaml}\nproviders: {bundled: []}\n")
    (tmp_path / "p.yaml").write_text(yaml.safe_dump({"aiGateway": {"use": "dry-run"}, "apps": {"targets": [str(APP)], "perfMode": ["latency", "throughput"]}}))
    (tmp_path / "s.yaml").write_text("schemaVersion: 1\nresults: r\nrun: {id: one}\ncrypto: {config: global.yaml}\nllm: {config: p.yaml}\n")
    return read_index(tmp_path / "s.yaml")


def lines_of():
    found = []
    return found, found.append


def runs(index):
    log = index.results / "runs.log"
    return log.read_text().splitlines() if log.is_file() else []


def test_the_child_cannot_be_decided_by_a_lookup(index, monkeypatch):
    monkeypatch.setenv("CRYPTOBENCH_CONFIG", "/no/such/global.yaml")
    monkeypatch.setenv("PERFREPAIR_CONFIG", "/no/such/perfrepair.yaml")
    env = phases.child_env(index, ROOT)
    assert "CRYPTOBENCH_CONFIG" not in env and env["PERFREPAIR_CONFIG"] == str(index.llm_config)
    assert env["CRYPTOBENCH_ROOT"] == str(ROOT)
    flags = phases.common_flags(index, "s.json", "o.json")
    assert flags[:4] == ["--perfrepair-config", str(index.llm_config), "--config", str(index.crypto_config)]


def test_both_phases_run_the_benchmark_once_and_the_second_on_the_first_ones_folder(index, monkeypatch, tmp_path):
    monkeypatch.setenv("CRYPTOBENCH_CONFIG", "/no/such/global.yaml")
    monkeypatch.setenv("PERFREPAIR_CONFIG", "/no/such/perfrepair.yaml")
    decoy = tmp_path / "home/.config/cryptobench/global.yaml"
    decoy.parent.mkdir(parents=True)
    decoy.write_text("schemaVersion: 1\nselection: {testSet: nope.yaml}\n")
    monkeypatch.setenv("HOME", str(decoy.parents[2]))
    found, echo = lines_of()
    code = phases.run_phases(index, {"tree": [{"key": "settings"}]}, root=FAKE_ROOT, echo=echo)
    device = index.results / DEVICE
    # every pipeline call names crypto.config or a file the guide derived from it inside the device folder
    configs = [pathlib.Path(line.split()[1]) for line in runs(index)]
    assert configs[0] == index.crypto_config and all(c.is_relative_to(device) for c in configs[1:])
    assert found[0] == f"facade crypto: crypto_ok: device {device}, run one"
    assert found[1].startswith("facade guided: guided_")
    assert code == (0 if found[1] == "facade guided: guided_ok" else 1)
    # a probe, then the benchmark: the guided phase adds no line
    assert len(runs(index)) == 2 and sum("--bench" in line for line in runs(index)) == 1
    record = json.loads((device / "runs/run_one.json").read_text())
    assert record["settings"] == {"tree": [{"key": "settings"}]} and record["id"] == "one"
    assert (device / "grouping/groups.json").is_file() and found[1] == "facade guided: guided_stopped: no_replacement exit=1"


def test_the_first_phase_alone_calls_no_model_and_measures_once(index):
    outcome = index.results.parent / "o.json"
    settings = index.results.parent / "t.json"
    settings.write_text("{}")
    flags = [*phases.common_flags(index, settings, outcome), *phases.crypto_flags(index)]
    done = subprocess.run([sys.executable, "-m", "perfrepair", "guide", *flags], env=phases.child_env(index, FAKE_ROOT), check=False,
                          capture_output=True, text=True)
    assert done.returncode == 0, done.stderr
    device = index.results / DEVICE
    assert json.loads(outcome.read_text()) == {"device": str(device), "run": "one", "exit": 0, "code": None}
    assert (device / "rows.json").is_file() and (device / "grouping/items.json").is_file()
    assert not (device / "grouping/groups.json").exists() and sum("--bench" in line for line in runs(index)) == 1
    assert "guide grouping" not in done.stdout and "guide targets" not in done.stdout


def test_a_first_phase_failure_stops_the_second(index, monkeypatch):
    monkeypatch.setenv("FAKE_INTERRUPT", "1")
    found, echo = lines_of()
    code = phases.run_phases(index, {}, root=FAKE_ROOT, echo=echo)
    assert code == 1 and found[0].startswith("facade crypto: crypto_failed: ") and "exit=1" in found[0]
    assert found[1:] == ["facade guided: guided_not_run: the crypto phase failed"]


def test_the_facade_reports_a_missing_dependency_friendly():
    probe = "import importlib.util, sys; sys.modules['yaml'] = None; importlib.util.find_spec = lambda name: None; import runpy; runpy.run_path(sys.argv[1], run_name='__main__')"
    done = subprocess.run([sys.executable, "-c", probe, str(ROOT / "scripts/facade.py"), "--settings", "x"], capture_output=True, text=True,
                          env={"PYTHONPATH": str(ROOT / "scripts")}, check=False)
    assert done.returncode == 1 and done.stderr.strip() == "error: missing_dependency: yaml; pip install -r requirements.txt"
