from pathlib import Path
from types import SimpleNamespace

import yaml

from perfrepair.device.measures import owned_config
from perfrepair.dto.perf_mode import GENERIC_MODE
from perfrepair.guide import app_steps as steps
from perfrepair.inputs import table


def _device_step(monkeypatch, app_config):
    seen = []
    monkeypatch.setattr(steps, "run_pipeline", lambda config, *a, **k: seen.append(config) or Path("m.yaml"))
    monkeypatch.setattr(steps, "report_invalid", lambda manifest, app: 0)
    g = SimpleNamespace(config=Path("device.yaml"), app_config=app_config, echo=print, app_id="a", device=Path("no-such-device"),
                        paths=SimpleNamespace(root=Path("r"), harness=Path("h.yaml")), mode=SimpleNamespace(perf=GENERIC_MODE))
    steps.device(g)
    return seen[0]


def test_the_app_step_runs_on_apps_benchmark_config(monkeypatch):
    assert _device_step(monkeypatch, Path("app.yaml")) == Path("app.yaml")


def test_unset_falls_back_to_the_device_config(monkeypatch):
    assert _device_step(monkeypatch, None) == Path("device.yaml")


def test_the_app_step_measures_what_its_own_perf_mode_needs_on_a_device(tmp_path):
    base = tmp_path / "global.yaml"
    base.write_text("schemaVersion: 1\nselection: {testSet: x.yaml}\nrun: {inputSizes: [64]}\n")
    made = owned_config(base, tmp_path / "app", GENERIC_MODE, on_device=True)
    assert made == tmp_path / "app" / "metrics-global.yaml"
    run = yaml.safe_load(made.read_text())["run"]
    assert run == {"inputSizes": [64], "metrics": ["TIME", "ALLOCATION"]}


def test_the_row_is_a_path_with_no_default():
    assert table.APPS_BENCHMARK_CONFIG.key == "apps.benchmarkConfig" and table.APPS_BENCHMARK_CONFIG.default is None
