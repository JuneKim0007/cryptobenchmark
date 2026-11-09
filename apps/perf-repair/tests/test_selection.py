from pathlib import Path

import yaml

from perfrepair import run_dir as rd
from perfrepair.device.selection import UNKNOWN, bundled_named, exclusions, lacking, section, write_config
from perfrepair.dto.device import DeviceRecord
from cryptobench.catalogue.grouping import Item
from perfrepair.dto.screen import Verdict

ITEMS = [Item(1, "TypeD", "H-1", "P1", "digest.none"), Item(2, "TypeD", "H1", "P1", "digest.none"),
         Item(3, "TypeD", "H2", "P1", "digest.none"), Item(4, "TypeD", "H1", "P2", "digest.none")]
VERDICTS = {1: Verdict("accepted", "r", canonical="H-1"), 2: Verdict("accepted", "r", canonical="H-1"),
            3: Verdict("accepted", "r", canonical="H-2"), 4: Verdict("accepted", "r", canonical="H-1")}


def record(items=None):
    return DeviceRecord("d", "host", {}, {"config": "base"}, "m", {}, section("gen", frozenset(items)) if items else {})


def test_an_excluded_spelling_of_a_kept_canonical_name_stays_and_other_providers_go():
    rules = exclusions(ITEMS, VERDICTS, frozenset({"TypeD|H-1|P1"}))
    assert rules == [{"provider": "P1", "type": "TypeD", "name": "H2"}, {"provider": "P2", "type": "TypeD", "name": "H1"}]


def test_a_bundled_item_counts_as_named_only_when_a_site_names_its_algorithm():
    named = bundled_named(ITEMS, VERDICTS, frozenset({"P2", "P1"}), [ITEMS[0]])
    assert named == {"TypeD|H-1|P1", "TypeD|H1|P1", "TypeD|H1|P2"}
    assert bundled_named(ITEMS, VERDICTS, frozenset({"P2"}), [ITEMS[2]]) == frozenset()


def test_a_used_set_that_grew_reruns_nothing_the_gate_measures_the_gap():
    assert lacking(record({"a", "b"}), "gen", "base") is None


def test_without_a_section_the_base_run_measured_everything_unless_the_manifest_is_another_config():
    assert lacking(record(), "base", "base") is None
    assert lacking(None, "gen", "base") == UNKNOWN


def test_the_used_set_adds_an_include_per_item_the_test_set_lacks_in_the_declared_spelling(tmp_path):
    base = tmp_path / "global.yaml"
    (tmp_path / "set.yaml").write_text("schemaVersion: 1\ninclude: [{type: T, name: A}]\noverrides: [{match: {type: T}, set: {keySizes: [1]}}]\n")
    base.write_text("schemaVersion: 1\nselection: {testSet: set.yaml}\n")
    adds = [{"provider": "P", "type": "T", "name": "A"}, {"provider": "P", "type": "K", "name": "hMacX"}]
    doc = yaml.safe_load(write_config(base, tmp_path, [], adds).read_text())
    added = yaml.safe_load(Path(doc["selection"]["testSet"]).read_text())
    assert Path(doc["selection"]["testSet"]) == tmp_path / rd.USED_TEST_SET
    assert added["include"] == [{"type": "T", "name": "A"}, *adds] and added["overrides"][0]["set"] == {"keySizes": [1]}
    assert "hMacX" not in (tmp_path / "set.yaml").read_text()


def test_an_empty_include_already_plans_everything_so_nothing_is_added(tmp_path):
    (tmp_path / "set.yaml").write_text("schemaVersion: 1\n")
    (tmp_path / "global.yaml").write_text("schemaVersion: 1\nselection: {testSet: set.yaml}\n")
    doc = yaml.safe_load(write_config(tmp_path / "global.yaml", tmp_path, [], [{"provider": "P", "type": "T", "name": "A"}]).read_text())
    assert Path(doc["selection"]["testSet"]) == (tmp_path / "set.yaml").resolve()


def test_the_generated_config_keeps_the_base_and_its_test_set_resolved(tmp_path):
    base = tmp_path / "conf" / "global.yaml"
    base.parent.mkdir()
    base.write_text("schemaVersion: 1\nselection: {testSet: sets/x.yaml, exclude: [{type: T}]}\n"
                    "providers: {bundled: [{artifact: 'g:a:1', create: A}]}\nrun: {seed: 3}\n")
    path = write_config(base, tmp_path, [{"provider": "P", "type": "T", "name": "N"}])
    doc = yaml.safe_load(path.read_text())
    assert path == tmp_path / rd.USED_CONFIG and doc["providers"] == {"bundled": [{"artifact": "g:a:1", "create": "A"}]}
    assert doc["run"] == {"seed": 3} and Path(doc["selection"]["testSet"]) == (base.parent / "sets/x.yaml").resolve()
    assert doc["selection"]["exclude"] == [{"type": "T"}, {"provider": "P", "type": "T", "name": "N"}]
