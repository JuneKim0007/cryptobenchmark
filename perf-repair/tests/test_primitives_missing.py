"""log/details/primitives_missing.yaml: the writer, its reasons, the pointer line, and the host's bundled step on the fake pipeline."""
import pytest
import yaml
from test_device_flows import (  # noqa: F401  the flows' fixtures
    CONSCRYPT,
    SHA,
    flow,
    guide,
    run_targets,
    scoped,
    target,
)

from perfrepair import run_dir as rd
from perfrepair.device import missing_rows
from perfrepair.device.missing_rows import (
    bundled_rows,
    measured_rows,
    not_screened_rows,
    site_rows,
    variant_rows,
)
from perfrepair.device.primitives_missing import MissingList
from perfrepair.dto.bundled import (
    APPLY,
    BundledPolicy,
    Coordinate,
    MissingProvider,
    Suggestion,
    Suggestions,
)
from perfrepair.dto.primitives_missing import (
    BUNDLED_MISSING,
    HOST_CANNOT_BUILD,
    SKIPPED,
    STOPPED,
    MissingRow,
    pointer_line,
)
from perfrepair.dto.site import SITES_SCHEMA_VERSION
from perfrepair.files import write_json
from perfrepair.log.read import read_events
from perfrepair.result.primitives import NotScreened, build_table
from perfrepair.run_dir import AppPaths, GroupingPaths
from perfrepair.stop import CODES, policy
from perfrepair.stop.codes import STOP


def row(primitive="Cipher AES", provider="P", reason="not_on_device", apps=("a",), sites=1, action=SKIPPED):
    return MissingRow(primitive, provider, reason, apps, sites, action, (), "do it")


def listed(device):
    return yaml.safe_load((device / rd.PRIMITIVES_MISSING).read_text())


def site(resolution, engine="Cipher", algorithm="AES", provider=None, missing=None):
    return {"engineType": engine, "resolution": resolution, "resolvedProvider": provider, "resolvedAlgorithm": algorithm,
            "canonicalAlgorithm": algorithm, "missing": missing}


def app_files(device, sites, facts=None, app="a"):
    paths = AppPaths(device, app)
    paths.root.mkdir(parents=True, exist_ok=True)
    write_json(paths.sites, {"schemaVersion": SITES_SCHEMA_VERSION, "app": app, "sites": sites})
    write_json(paths.facts, facts or {})


def test_open_leaves_an_empty_list_over_a_stale_file(tmp_path):
    stale = tmp_path / rd.PRIMITIVES_MISSING
    stale.parent.mkdir(parents=True)
    stale.write_text("schemaVersion: 1\nrun: old\nmissing: [{primitive: x}]\n")
    MissingList().open(tmp_path)
    doc = listed(tmp_path)
    assert doc["schemaVersion"] == 1 and doc["run"] != "old" and doc["missing"] == []


def test_a_source_replaces_itself_and_rows_merge_across_sources(tmp_path):
    missing = MissingList()
    missing.open(tmp_path)
    missing.put("sites a", [row()])
    missing.put("sites a", [row()])
    missing.put("sites b", [row(apps=("b",), sites=2, action=STOPPED)])
    [merged] = listed(tmp_path)["missing"]
    assert merged["apps"] == ["a", "b"] and merged["sites"] == 3 and merged["action"] == STOPPED


def test_the_pointer_is_one_event_and_announced_only_with_rows(tmp_path, capsys):
    missing, said = MissingList(), []
    missing.open(tmp_path)
    missing.announce(said.append)
    assert said == []
    missing.put("one", [row()])
    missing.put("two", [row(primitive="Cipher DES")])
    missing.announce(said.append)
    assert said == [pointer_line(tmp_path / rd.PRIMITIVES_MISSING)]
    assert said[0] == f"## to check primitives skipped or stopped due to not downloading them go {tmp_path}/log/details/primitives_missing.yaml"


def test_unbound_it_keeps_rows_and_writes_nothing(tmp_path):
    missing, said = MissingList(), []
    missing.put("one", [row()])
    missing.announce(said.append)
    assert len(missing.rows()) == 1 and said == [] and missing.path is None


def test_every_unscreened_name_is_reported_with_the_count_and_the_first():
    rows = [type("R", (), {"type": "Cipher", "algorithm": a, "provider": "P", "inputSize": 1, "rowId": a})() for a in ("Z", "B", "B")]
    with pytest.raises(NotScreened) as e:
        build_table(rows, {}, {})
    assert e.value.names == ("Cipher|B|P", "Cipher|Z|P") and e.value.code == "primitive_not_screened"
    assert str(e.value).startswith("primitive_not_screened: 2 measured primitives have no screen.json verdict, first Cipher|B|P")
    assert "all in /x/y" in str(NotScreened(e.value.names, "/x/y"))


def test_a_not_on_device_site_follows_its_setting_and_an_absent_one_only_skips(tmp_path, monkeypatch):
    app_files(tmp_path, [site("not_on_device", provider="BC", missing="BC"), site("not_on_device", provider="BC", missing="BC")],
              {"bundled": [{"artifact": "g:bc", "providerName": "BC", "version": "1"}]})
    app_files(tmp_path, [site("not_on_device", algorithm="X", missing="Cipher X")], app="b")
    [named] = site_rows(tmp_path, "a")
    [absent] = site_rows(tmp_path, "b")
    assert (named.reason, named.provider, named.sites, named.action, named.coordinates) == ("not_on_device", "BC", 2, SKIPPED, ("g:bc:1",))
    assert (absent.reason, absent.provider, absent.primitive, absent.action) == ("absent_on_device", None, "Cipher X", SKIPPED)
    policy.install(lambda code: STOP)
    try:
        assert site_rows(tmp_path, "a")[0].action == STOPPED and site_rows(tmp_path, "b")[0].action == SKIPPED
    finally:
        policy.reset()


def test_a_site_on_a_device_provider_no_item_holds_is_listed(tmp_path, monkeypatch):
    app_files(tmp_path, [site("explicit", provider="P"), site("default", algorithm="B", provider="P")])
    GroupingPaths(tmp_path).items.parent.mkdir(parents=True)
    write_json(GroupingPaths(tmp_path).items, {})
    monkeypatch.setattr(missing_rows, "read_items", lambda _: [type("I", (), {"qualified": "Cipher|B|P"})()])
    [lost] = site_rows(tmp_path, "a")
    assert (lost.reason, lost.primitive, lost.provider) == ("no_device_item", "Cipher AES", "P")


def test_the_run_log_names_a_site_item_never_measured_unless_a_case_of_it_was(tmp_path):
    app_files(tmp_path, [site("default", provider="P"), site("default", algorithm="B", provider="P")])
    entry = {"stage": "trial", "provider": "P", "type": "Cipher", "occurrences": 1, "rowIds": []}
    write_json(tmp_path / rd.RUN_LOG, {"schemaVersion": 1, "entries": [
        {**entry, "status": "not_runnable", "algorithm": "AES", "reason": "needs_a_key_in_the_store"},
        {**entry, "status": "skipped", "algorithm": "B", "reason": "one_size"}, {**entry, "status": "measured", "algorithm": "B", "reason": None}]})
    [lost] = measured_rows(tmp_path, "a")
    assert (lost.reason, lost.primitive, lost.action) == ("not_measured", "Cipher AES", SKIPPED)
    assert lost.next == "the benchmark did not measure it: needs_a_key_in_the_store"


def test_a_scope_measured_only_in_the_other_variant_is_listed(tmp_path, monkeypatch):
    scopes = [{"id": "s1", "engineType": "Cipher", "algorithm": "AES", "provider": "P"}, {"id": "s2", "engineType": "Cipher", "algorithm": "B", "provider": "P"}]
    monkeypatch.setattr(missing_rows.rd, "read_scopes", lambda _: {"scopes": scopes})
    [lost] = variant_rows(tmp_path, "a", [{"scope": "s1", "reason": "variant_not_measured"}, {"scope": "s2", "reason": "no_gain"}])
    assert (lost.reason, lost.primitive, lost.sites) == ("variant_not_measured", "Cipher AES", 1)


def test_not_screened_rows_list_every_name_and_the_apps_using_it(tmp_path):
    app_files(tmp_path, [site("default", provider="P")])
    used, unused = not_screened_rows(tmp_path, ("Cipher|AES|P", "Cipher|Z|Q"), ["a"])
    assert (used.apps, used.sites, used.action, used.reason) == (("a",), 1, STOPPED, "not_screened")
    assert (unused.apps, unused.sites) == ((), 0) and unused.next == CODES["primitive_not_screened"].next


def _found(*kinds):
    coordinate = Coordinate("g:p", (("a", "1"),))
    matched = Suggestion("P", "g:p", "1", ("a",), entry={"artifact": "g:p:1", "create": "X"}, applied=False)
    return Suggestions((MissingProvider("P", ("a",), (coordinate,), 2),), matched=(matched,) if "matched" in kinds else ())


@pytest.mark.parametrize("policy_, on_device, configured, kinds, reason", [
    (BundledPolicy(APPLY), False, frozenset(), ("matched",), HOST_CANNOT_BUILD),
    (BundledPolicy(), False, frozenset({"g:p"}), (), HOST_CANNOT_BUILD),
    (BundledPolicy("suggest"), False, frozenset(), ("matched",), BUNDLED_MISSING),
    (BundledPolicy(APPLY), True, frozenset(), (), BUNDLED_MISSING)])
def test_a_provider_row_says_when_the_host_cannot_build_it(policy_, on_device, configured, kinds, reason):
    [r] = bundled_rows(_found(*kinds), policy_, on_device, configured)
    assert (r.reason, r.provider, r.primitive, r.sites, r.coordinates) == (reason, "P", None, 2, ("g:p:1",))
    assert ("--device" in r.next) == (reason == HOST_CANNOT_BUILD)


def _pointers(flow_):
    return [e for e in read_events(flow_.device / rd.EVENTS) if e.data.get("pointer")]


def test_host_apply_says_nothing_is_applied_and_lists_the_row(scoped, capsys):  # noqa: F811
    scoped.bundled = {"fromApps": "apply"}
    root = target(scoped, "tls", SHA, ships=CONSCRYPT)
    lines = run_targets(scoped, root)
    said = next(line for line in lines if line.startswith("device bundled: "))
    assert "applied 0" in said and said.endswith("nothing applied: only a --device run builds and installs bundled providers")
    assert not (scoped.device / rd.BUNDLED_CONFIG).exists()
    assert not any("the probe does not hold" in line for line in lines)
    rows = {r["provider"]: r for r in listed(scoped.device)["missing"] if r["primitive"] is None}
    assert rows["Conscrypt"]["reason"] == HOST_CANNOT_BUILD and rows["Conscrypt"]["coordinates"] == [CONSCRYPT]
    assert rows["BC"]["reason"] == BUNDLED_MISSING and "duplicate_name" in rows["BC"]["next"]
    # one probe, one benchmark: the rerun only a device's probe can answer is gone
    assert scoped.device_runs() == 2


def test_host_with_a_configured_provider_does_not_probe_again(scoped):  # noqa: F811
    scoped.global_yaml.write_text(scoped.global_yaml.read_text().replace("bundled: []", f"bundled: [{{artifact: '{CONSCRYPT}', create: X}}]"))
    root = target(scoped, "tls", SHA, ships=CONSCRYPT)
    lines = run_targets(scoped, root)
    assert not any("the probe does not hold" in line for line in lines)
    rows = {r["provider"]: r for r in listed(scoped.device)["missing"] if r["primitive"] is None}
    assert rows["Conscrypt"]["reason"] == HOST_CANNOT_BUILD


def _guide_out(flow_, capsys, root):
    """The guide's whole stdout, which run_targets filters."""
    path = flow_.settings()
    document = yaml.safe_load(path.read_text())
    document["apps"] = {"targets": [str(root)], "perfMode": ["latency", "throughput"]}
    path.write_text(yaml.safe_dump(document))
    guide(["--agent", "dry-run", "--perfrepair-config", str(path)])
    return capsys.readouterr().out.splitlines()


def test_the_pointer_is_the_last_line_when_the_guide_finishes(scoped, capsys):  # noqa: F811
    out = _guide_out(scoped, capsys, scoped.sha)
    pointer = pointer_line(scoped.device / rd.PRIMITIVES_MISSING)
    assert out[-1] == pointer and out.count(pointer) == 1 and any(line.startswith("app ") for line in out)


def test_the_pointer_is_the_last_line_when_the_guide_stops(scoped, capsys):  # noqa: F811
    scoped.bundled = {"onMissing": "stop"}
    out = _guide_out(scoped, capsys, scoped.sha)
    pointer = pointer_line(scoped.device / rd.PRIMITIVES_MISSING)
    assert out[-1] == pointer and out.count(pointer) == 1 and len(_pointers(scoped)) == 1
    status = (scoped.device / rd.STATUS_LOG).read_text().splitlines()
    assert status.count(pointer) == 1
    assert [r["action"] for r in listed(scoped.device)["missing"] if r["provider"] == "BC" and r["primitive"] is None] == [STOPPED]


def test_a_clean_rerun_empties_the_list_and_says_nothing(scoped, capsys):  # noqa: F811
    _guide_out(scoped, capsys, scoped.sha)
    assert listed(scoped.device)["missing"] != []
    # with the filter off no bundled step runs, and this app's site resolves
    scoped.filter = False
    out = _guide_out(scoped, capsys, scoped.sha)
    assert listed(scoped.device)["missing"] == []
    assert not any(line.startswith("## ") for line in out)


def test_not_screened_stops_with_every_name_listed_and_next_naming_the_file(scoped, capsys, monkeypatch):  # noqa: F811
    from perfrepair.device import primitives
    scoped.bundled = {}
    monkeypatch.setattr(primitives, "status_of", lambda _: {})
    lines = run_targets(scoped, scoped.sha)
    path = scoped.device / rd.PRIMITIVES_MISSING
    stop = next(line for line in lines if line.startswith("guide prerequisites: stop prerequisites_failed: "))
    assert "primitive_not_screened: " in stop and f"all in {path}" in stop and " measured primitives have no screen.json verdict, first " in stop
    rows = [r for r in listed(scoped.device)["missing"] if r["reason"] == "not_screened"]
    assert len(rows) > 1 and {r["action"] for r in rows} == {STOPPED}
    failed = next(line for line in (scoped.device / rd.STATUS_LOG).read_text().splitlines() if line.startswith("prerequisites_failed "))
    assert failed.endswith(f"next: read {path}; {CODES['primitive_not_screened'].next}")
