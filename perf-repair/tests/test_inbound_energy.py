"""data_handler/inbound/energy.py: the invalid cases of every energy.json a manifest lists."""
import json

from perfrepair.data_handler.inbound.energy import invalid_cases


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
