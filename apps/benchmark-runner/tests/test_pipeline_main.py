"""pipeline.main's stage order per run kind, every stage replaced by a recorder."""
import argparse

import pytest

import pipeline
from cryptobench.shared.errors.failures import CommandError

FLAGS = {"probe": False, "identify": False, "devices": False, "check_session": None, "session": None, "per_suite": False, "interop": None, "harness": None, "check": False, "bench": False, "device": False,
         "config": None, "results": None, "stream": False, "stacktrace": False, "suppress_errors": ""}


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
    monkeypatch.setattr(pipeline.config_check, "parsed", recorder("config_check", {"bundled": []}))
    monkeypatch.setattr(pipeline.dependencies, "check", recorder("dependencies"))
    monkeypatch.setattr(pipeline, "Device", Device)
    monkeypatch.setattr(pipeline.paths, "repo", lambda: pipeline.paths.Repo(tmp_path))
    for name in ("list_devices", "identify", "harness_run", "interop_run", "check_run", "manifest"):
        monkeypatch.setattr(pipeline, name, recorder(name))
    monkeypatch.setattr(pipeline, "measure_cases", recorder("measure_cases", (False, [], 1)))
    monkeypatch.setattr(pipeline, "checked_folder", recorder("checked_folder"))
    monkeypatch.setattr(pipeline.results_layout, "warn_if_temp", recorder("warn_if_temp"))
    monkeypatch.setattr(pipeline, "discover_published", recorder("discover_published", (tmp_path, (None, None, None, None, {}))))
    monkeypatch.setattr(pipeline.guide, "write", recorder("guide"))

    def run(**flags):
        monkeypatch.setattr(pipeline, "parse_options", lambda: argparse.Namespace(**{**FLAGS, **flags}))
        seen.clear()
        pipeline.main()
        return list(seen)
    return run


START = ["global_config", "config_check", "dependencies"]


@pytest.mark.parametrize("flags, order", [
    ({}, START + ["warn_if_temp", "discover_published", "guide", "manifest"]),
    ({"probe": True}, START + ["warn_if_temp", "discover_published", "guide", "manifest"]),
    ({"probe": True, "device": True}, START + ["Device", "connect", "warn_if_temp", "discover_published", "guide", "manifest"]),
    ({"bench": True}, START + ["warn_if_temp", "discover_published", "guide", "measure_cases", "manifest"]),
    ({"device": True}, START + ["Device", "connect", "warn_if_temp", "discover_published", "guide", "measure_cases", "manifest"]),
    ({"check": True, "bench": True}, START + ["warn_if_temp", "check_run"]),
    ({"interop": "plan.yaml", "bench": True}, START + ["warn_if_temp", "interop_run"]),
    ({"harness": "harness.yaml", "device": True}, START + ["Device", "connect", "checked_folder", "harness_run"]),
    ({"identify": True}, ["global_config", "dependencies", "identify"]),
    ({"identify": True, "device": True}, ["global_config", "dependencies", "Device", "connect", "identify"]),
    ({"devices": True}, ["list_devices"]),
], ids=["plain", "probe", "probe device", "bench", "device", "check", "interop", "harness", "identify", "identify device", "devices"])
def test_the_stages_of_each_run_kind_in_order(calls, flags, order):
    assert calls(**flags) == order


def test_interop_wins_over_check_when_parse_options_lets_both_through(calls):
    assert calls(interop="plan.yaml", check=True, bench=True)[-1] == "interop_run"


def test_a_check_without_bench_or_device_is_refused_before_discovery(calls, monkeypatch):
    monkeypatch.setattr(pipeline, "discover_published", lambda *_arguments: pytest.fail("discovered"))
    with pytest.raises(CommandError, match="^--check: "):
        calls(check=True)


def test_per_suite_places_the_run_under_the_test_sets_stem(calls, monkeypatch, tmp_path):
    seen = {}
    monkeypatch.setattr(pipeline.config_check, "parsed", lambda _configuration: {"bundled": [], "testSet": str(tmp_path / "sets/tier1.yaml")})

    def published(*arguments):
        seen["suite"] = arguments[-1]
        return tmp_path, (None, None, None, None, {})
    monkeypatch.setattr(pipeline, "discover_published", published)
    calls(per_suite=True)
    assert seen == {"suite": "tier1"}
    calls()
    assert seen == {"suite": None}
