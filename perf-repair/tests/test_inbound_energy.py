"""data_handler/inbound/energy.py: the invalid cases of every energy.json a manifest lists."""
import json

import logging

from perfrepair.data_handler.inbound.energy import invalid_cases
from perfrepair.device.energy import report_invalid
from perfrepair.log.emit import EVENT_ATTR


def _energy(path, cases):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"cases": cases}))


def test_each_listed_file_gives_its_invalid_cases_and_a_missing_one_none(tmp_path):
    _energy(tmp_path / "p1/energy.json", {"c1": {"valid": True, "invalid": []},
                                          "c2": {"valid": False, "invalid": ["short_window", "window_uncovered"]}})
    _energy(tmp_path / "p2/energy.json", {"c3": {"valid": False, "invalid": ["short_window"]}})
    (tmp_path / "manifest.yaml").write_text("files:\n  energy: [p1/energy.json, p2/energy.json, p3/energy.json]\n")
    found = invalid_cases(tmp_path / "manifest.yaml")
    assert [(c.case, c.reasons, c.file.parent.name) for c in found] == [
        ("c2", ("short_window", "window_uncovered"), "p1"), ("c3", ("short_window",), "p2")]


def test_a_manifest_without_energy_has_no_case(tmp_path):
    (tmp_path / "manifest.yaml").write_text("schemaVersion: 1\nmode: device\n")
    assert invalid_cases(tmp_path / "manifest.yaml") == []


def _findings(caplog):
    return [getattr(r, EVENT_ATTR) for r in caplog.records if hasattr(r, EVENT_ATTR)]


def test_a_case_invalid_in_several_processes_is_one_finding(tmp_path, caplog):
    for name in ("p1", "p2"):
        _energy(tmp_path / name / "energy.json", {"c": {"valid": False, "invalid": ["short_window"]}})
    (tmp_path / "manifest.yaml").write_text("files:\n  energy: [p1/energy.json, p2/energy.json]\n")
    with caplog.at_level(logging.INFO, logger="perfrepair.event"):
        assert report_invalid(tmp_path / "manifest.yaml") == 1
    found = _findings(caplog)
    assert [(f["item"], f["outcome"]) for f in found] == [("c", "short_window")] and found[0]["data"]["processes"] == 2


def test_an_unreadable_energy_file_is_a_finding_and_no_failure(tmp_path, caplog):
    (tmp_path / "energy.json").write_text("{not json")
    (tmp_path / "manifest.yaml").write_text("files:\n  energy: energy.json\n")
    with caplog.at_level(logging.INFO, logger="perfrepair.event"):
        assert report_invalid(tmp_path / "manifest.yaml") == 0
    assert [f["outcome"] for f in _findings(caplog)] == ["energy_unreadable"]
