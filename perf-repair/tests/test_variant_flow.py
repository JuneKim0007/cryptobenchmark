"""#91 end to end on the fake pipeline: a benchmark.json with both variants under suffixed case ids, through inbound,
primitives.tsv and dossiers; a scope reads only its pattern's variant."""
import shutil

import pytest
from test_device_flows import APP, F, Flow, run_targets

from perfrepair import run_dir as rd
from perfrepair.app.facts.path_id import path_id
from perfrepair.dto.primitives import PrimitivesTable
from perfrepair.files import read_json

GCM = 'javax.crypto.Cipher.getInstance("AES/GCM/NoPadding", "Slow")'
SOURCE = f"""package demo;

import javax.crypto.Cipher;

class Uses {{
    private Cipher held;

    void open(java.security.Key key) throws Exception {{
        held = {GCM};
        held.init(Cipher.ENCRYPT_MODE, key);
    }}

    byte[] seal(byte[] data) throws Exception {{
        return held.doFinal(data);
    }}

    byte[] once(byte[] data, java.security.Key key) throws Exception {{
        Cipher c = {GCM};
        c.init(Cipher.ENCRYPT_MODE, key);
        return c.doFinal(data);
    }}
}}
"""


@pytest.fixture
def flow(tmp_path, capsys, monkeypatch):
    monkeypatch.setenv("CRYPTOBENCH_ROOT", str(F / "device"))
    monkeypatch.setenv("FAKE_VARIANTS", "1")
    return Flow(tmp_path, capsys)


def _app(flow):
    root = flow.tmp / "apps" / "gcm"
    shutil.copytree(APP, root, ignore=shutil.ignore_patterns("java", "kotlin"))
    (root / "src/main/java/demo").mkdir(parents=True)
    (root / "src/main/java/demo/Uses.java").write_text(SOURCE)
    return root


def _has_parser() -> bool:
    try:
        import tree_sitter_java  # noqa: F401
    except ImportError:
        return False
    return True


def _ratio(device, variant: str) -> float:
    rows, m = read_json(device / rd.ROWS)["rows"], read_json(device / rd.MEASUREMENTS)["measurements"]
    median = {r["provider"]: m[r["rowId"]]["timeNs"]["median"] for r in rows
              if r["variant"] == variant and r["type"] == "Cipher" and r["operation"] == "ENCRYPT"}
    return median["Fast"] / median["Slow"]


def test_both_variants_reach_every_stage_apart_and_a_scope_reads_its_own(flow):
    root = _app(flow)
    run_targets(flow, root)
    rows = read_json(flow.device / rd.ROWS)["rows"]
    assert {(r["rowId"].rsplit("_", 1)[1], r["variant"], r["perCall"]) for r in rows} == {
        ("fixed", "fixed", "initAndOperation"), ("notFixed", "notFixed", "getInstanceInitAndOperation")}
    assert {line.variant for line in PrimitivesTable.from_tsv((flow.device / rd.PRIMITIVES).read_text()).lines} == {
        "fixed", "notFixed"}
    paths = rd.AppPaths(flow.device, path_id(root))
    pattern = {s["function"]: s["pattern"] for s in read_json(paths.scopes)["scopes"]}
    assert pattern == {"open": "fixed" if _has_parser() else "notFixed", "once": "notFixed"}
    doc = read_json(paths.dossiers)
    found = {}
    for d in doc["dossiers"]:
        [time] = [e for o in d["options"] if o["item"].endswith("|Fast") for e in o["estimates"] if e["metric"] == "timeNs"]
        assert time["ratio"] == pytest.approx(_ratio(flow.device, d["scope"]["pattern"]), rel=0.05)
        found[d["scope"]["function"]] = d["perCall"]
    assert found["once"] == ["getInstanceInitAndOperation"]
    # the fixed variant makes the option slower: the held cipher is offered nothing, the per-call one is
    assert ("open" in found) is not _has_parser()
    assert [n["reason"] for n in doc["noOptions"]] == (["no_gain"] if _has_parser() else [])
    assert _ratio(flow.device, "fixed") != pytest.approx(_ratio(flow.device, "notFixed"), rel=0.05)
    assert flow.problems() == {}


def test_a_fixed_scope_has_no_truth_check_because_its_function_is_the_setup():
    from perfrepair.result.category import checkable
    assert not checkable({"pattern": "fixed"}) and checkable({"pattern": "notFixed"})
