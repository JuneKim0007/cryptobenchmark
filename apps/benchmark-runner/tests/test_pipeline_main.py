"""pipeline.main's stage order per run kind, every stage replaced by a recorder."""
import argparse

import pytest

import pipeline

FLAGS = {"probe": False, "identify": False, "interop": None, "harness": None, "check": False, "bench": False, "device": False,
         "config": None, "results": None, "stream": False, "stacktrace": False}


@pytest.fixture
def calls(monkeypatch, tmp_path):
    seen = []

    def recorder(name, result=None):
        def record(*_arguments, **_options):
            seen.append(name)
            return result
        return record

    class Device:
        def __init__(self, *_arguments):
            seen.append("Device")

        def connect(self):
            seen.append("connect")

    monkeypatch.setattr(pipeline, "global_config", recorder("global_config", tmp_path / "global.yaml"))
    monkeypatch.setattr(pipeline.config_check, "parsed", recorder("config_check"))
    monkeypatch.setattr(pipeline.dependencies, "check", recorder("dependencies"))
    monkeypatch.setattr(pipeline, "Device", Device)
    monkeypatch.setattr(pipeline.paths, "repo", lambda: pipeline.paths.Repo(tmp_path))
    for name in ("identify", "harness_run", "interop_run", "check_run", "measure_cases", "manifest"):
        monkeypatch.setattr(pipeline, name, recorder(name))
    monkeypatch.setattr(pipeline, "checked_folder", recorder("checked_folder"))
    monkeypatch.setattr(pipeline.results_layout, "warn_if_temp", recorder("warn_if_temp"))
    monkeypatch.setattr(pipeline, "device_discover", recorder("device_discover", (tmp_path, (None, None, None, None, {}))))

    def run(**flags):
        monkeypatch.setattr(pipeline, "parse_options", lambda: argparse.Namespace(**{**FLAGS, **flags}))
        seen.clear()
        pipeline.main()
        return list(seen)
    return run


START = ["global_config", "config_check", "dependencies"]


@pytest.mark.parametrize("flags, order", [
    ({}, START + ["warn_if_temp", "device_discover", "manifest"]),
    ({"probe": True}, START + ["warn_if_temp", "device_discover", "manifest"]),
    ({"probe": True, "device": True}, START + ["Device", "connect", "warn_if_temp", "device_discover", "manifest"]),
    ({"bench": True}, START + ["warn_if_temp", "device_discover", "measure_cases", "manifest"]),
    ({"device": True}, START + ["Device", "connect", "warn_if_temp", "device_discover", "measure_cases", "manifest"]),
    ({"check": True, "bench": True}, START + ["warn_if_temp", "check_run"]),
    ({"interop": "plan.yaml", "bench": True}, START + ["warn_if_temp", "interop_run"]),
    ({"harness": "harness.yaml", "device": True}, START + ["Device", "connect", "checked_folder", "harness_run"]),
    ({"identify": True}, ["global_config", "dependencies", "identify"]),
    ({"identify": True, "device": True}, ["global_config", "dependencies", "Device", "connect", "identify"]),
], ids=["plain", "probe", "probe device", "bench", "device", "check", "interop", "harness", "identify", "identify device"])
def test_the_stages_of_each_run_kind_in_order(calls, flags, order):
    assert calls(**flags) == order


def test_interop_wins_over_check_when_parse_options_lets_both_through(calls):
    assert calls(interop="plan.yaml", check=True, bench=True)[-1] == "interop_run"
