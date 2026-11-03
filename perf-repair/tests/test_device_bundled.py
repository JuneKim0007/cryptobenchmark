"""device.bundled: the missing set, its catalog suggestions, the suggestions validator and the one warn-or-stop."""
import json

import pytest

import yaml

from perfrepair.catalog.bundled_providers import BundledCatalog, BundledRow
from perfrepair.device.bundled_config import bundled_config, harness_config
from perfrepair.device.bundled_missing import missing_set
from perfrepair.device.bundled_policy import DeviceHalt, act
from perfrepair.device.bundled_suggest import suggest
from perfrepair.dto.bundled import OFF, BundledPolicy, Coordinate, MissingProvider, entries_digest
from perfrepair.dto.version import newest
from perfrepair.inputs.check import check_from_apps
from perfrepair.validation.bundled import validate_suggestions

CATALOG = BundledCatalog({
    "g:aaa": BundledRow("g:aaa", "Aaa", "g.Aaa#make", "S", alias="BundledAaa", notes="seen once"),
    "g:aaa-old": BundledRow("g:aaa-old", "Aaa", "g.Aaa#make", "S", alias="BundledAaa"),
    "g:bbb": BundledRow("g:bbb", "Bbb", "g.Bbb", "S", blocked="harness duplicate_name"),
})


def app(device, name, bundled=(), sites=()):
    folder = device / name
    folder.mkdir(parents=True)
    (folder / "app.json").write_text(json.dumps({"bundled": [
        {"artifact": a, "providerName": p, "version": v} for a, p, v in bundled]}))
    (folder / "sites.json").write_text(json.dumps({"sites": [
        {"resolution": r, "resolvedProvider": p} for r, p in sites]}))


def test_the_missing_set_is_what_neither_the_device_nor_the_config_holds(tmp_path):
    app(tmp_path, "one", [("g:aaa", "Aaa", "1.2"), ("g:plat", "Plat", "3"), ("g:conf", "Conf", "1"), ("g:lib", None, "1")])
    app(tmp_path, "two", [("g:aaa", "Aaa", "1.10")], [("not_on_device", "Ccc"), ("not_on_device", "Ccc"), ("default", "X")])
    found = missing_set(tmp_path, ["one", "two", "absent"], frozenset({"Plat"}), frozenset({"g:conf"}))
    assert found == [MissingProvider("Aaa", ("one", "two"), (Coordinate("g:aaa", (("one", "1.2"), ("two", "1.10"))),)),
                     MissingProvider("Ccc", ("two",), (), 2)]
    assert found[0].coordinates[0].version == "1.10"


def test_suggest_matches_blocks_and_never_guesses():
    missing = [MissingProvider("Aaa", ("a",), (Coordinate("g:aaa", (("a", "1.0"),)), Coordinate("g:aaa-old", (("a", "0.9"),)))),
               MissingProvider("Bbb", ("b",), (Coordinate("g:bbb", (("b", "2"),)),)),
               MissingProvider("Ccc", ("c",), ()),
               MissingProvider("Ddd", ("d",), (Coordinate("g:ddd", (("d", "1"),)),)),
               MissingProvider("Eee", ("e",), (Coordinate("g:aaa", (("e", None),)),))]
    found = suggest(missing, CATALOG, apply=True)
    assert [(s.artifact, s.entry, s.notes) for s in found.matched] == [
        ("g:aaa", {"artifact": "g:aaa:1.0", "create": "g.Aaa#make", "alias": "BundledAaa"}, "seen once")]
    assert [(s.provider, s.reason) for s in found.blocked] == [("Bbb", "harness duplicate_name")]
    assert [(s.provider, s.reason) for s in found.unmatched] == [
        ("Aaa", "name_taken"), ("Ccc", "no_coordinates"), ("Ddd", "no_catalog_row"), ("Eee", "no_catalog_row")]
    assert [m.provider for m in found.left()] == ["Bbb", "Ccc", "Ddd", "Eee"]
    assert validate_suggestions(found.to_json("apply", "c.yaml")) == []


def test_a_matched_row_without_a_pinned_version_is_unmatched():
    found = suggest([MissingProvider("Aaa", ("a",), (Coordinate("g:aaa", (("a", "$v"),)),))], CATALOG, apply=True)
    assert [(s.reason, s.entry) for s in found.unmatched] == [("no_pinned_version", None)] and not found.applied


def test_suggest_without_apply_applies_nothing():
    found = suggest([MissingProvider("Aaa", ("a",), (Coordinate("g:aaa", (("a", "1"),)),))], CATALOG, apply=False)
    assert found.matched and not found.applied and [m.provider for m in found.left()] == ["Aaa"]
    assert validate_suggestions(found.to_json("suggest", "c.yaml")) == []


def good():
    found = suggest([MissingProvider("Aaa", ("a",), (Coordinate("g:aaa", (("a", "1"),)),)),
                     MissingProvider("Bbb", ("b",), (Coordinate("g:bbb", (("b", "2"),)),))], CATALOG, apply=True)
    return found.to_json("apply", "c.yaml")


@pytest.mark.parametrize("change, problem", [
    (lambda d: d.update(fromApps="off"), "fromApps 'off' writes no suggestions"),
    (lambda d: d["counts"].update(applied=0), "counts.applied 0, the file lists 1"),
    (lambda d: d["blocked"][0].update(applied=True), "blocked[0]: applied on a blocked row"),
    (lambda d: d["blocked"][0].pop("reason"), "blocked[0]: no reason"),
    (lambda d: d["matched"][0]["entry"].update(artifact="g:aaa:9"), "matched[0]: entry artifact 'g:aaa:9' is not g:aaa:1"),
    (lambda d: d.update(fromApps="suggest"), "matched[0]: applied with fromApps suggest"),
    (lambda d: d["matched"][0].update(apps=[]), "matched[0]: apps is not a non-empty list of app ids"),
])
def test_each_bad_suggestions_file_names_its_problem_first(change, problem):
    doc = good()
    change(doc)
    assert validate_suggestions(doc)[0] == problem


def test_act_warns_or_stops_with_one_code(tmp_path):
    echoed = []
    act("bundled_missing", "Aaa", ["Aaa"], "warn", tmp_path, echoed.append)
    assert echoed == ["device bundled_missing: warn: Aaa"]
    with pytest.raises(DeviceHalt) as e:
        act("bundled_missing", "Aaa", ["Aaa"], "stop", tmp_path, echoed.append)
    assert (e.value.code, e.value.folder) == ("bundled_missing", tmp_path) and len(echoed) == 1


def test_newest_follows_gradle_order_over_pinned_versions_only():
    assert newest(["1.9", "1.10", "1.+", None, "$v"]) == "1.10" and newest([None]) is None
    assert entries_digest([]) is None and entries_digest([{"a": 1}]) == entries_digest([{"a": 1}])


def test_a_bare_off_in_yaml_is_off_with_no_warning():
    value = yaml.safe_load("fromApps: off")["fromApps"]
    check_from_apps("device.bundled.fromApps", value)
    assert BundledPolicy.read("warn", value).fromApps == OFF


def applied_folder(tmp_path):
    device, base = tmp_path / "device", tmp_path / "global.yaml"
    device.mkdir()
    base.write_text("selection: {testSet: t.yaml}\nproviders: {bundled: [{artifact: 'g:own:1', create: Own}]}\n")
    return device, base


def test_applied_entries_append_to_the_base_and_none_use_it_as_it_is(tmp_path):
    device, base = applied_folder(tmp_path)
    made = bundled_config(base, device, [{"artifact": "g:aaa:1", "create": "Aaa"}])
    document = yaml.safe_load(made.read_text())
    assert [e["artifact"] for e in document["providers"]["bundled"]] == ["g:own:1", "g:aaa:1"]
    assert document["selection"]["testSet"] == str(tmp_path / "t.yaml")
    assert bundled_config(base, device, []) == base and not made.exists()


def test_the_harness_builds_what_the_device_stage_applied(tmp_path):
    device, base = applied_folder(tmp_path)
    assert harness_config(device, None, tmp_path) is None and harness_config(device, base, tmp_path) == base
    made = bundled_config(base, device, [{"artifact": "g:aaa:1", "create": "Aaa"}])
    entry = {"artifact": "g:aaa:1", "create": "Aaa"}
    (device / "bundled-suggestions.yaml").write_text(yaml.safe_dump({"matched": [{"applied": True, "entry": entry}]}))
    assert harness_config(device, None, tmp_path) == made
    app_folder = tmp_path / "app"
    lighter = yaml.safe_load(harness_config(device, base, app_folder).read_text())
    assert [e["artifact"] for e in lighter["providers"]["bundled"]] == ["g:own:1", "g:aaa:1"]
