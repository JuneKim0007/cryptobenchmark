from pathlib import Path

import yaml

from perfrepair import run_dir as rd
from perfrepair.device.selection import UNKNOWN, exclusions, lacking, section, write_config
from perfrepair.dto.device import DeviceRecord
from perfrepair.dto.grouping import Item
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


def test_a_set_that_only_shrank_lacks_nothing_and_one_that_grew_names_how_many():
    done = record({"a", "b"})
    assert lacking(frozenset({"a"}), done, "gen", "base") is None
    assert lacking(frozenset({"a", "c", "d"}), done, "gen", "base") == "2 used items not measured"


def test_without_a_section_the_base_run_measured_everything_unless_the_manifest_is_another_config():
    assert lacking(frozenset({"a"}), record(), "base", "base") is None
    assert lacking(frozenset({"a"}), None, "gen", "base") == UNKNOWN


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
