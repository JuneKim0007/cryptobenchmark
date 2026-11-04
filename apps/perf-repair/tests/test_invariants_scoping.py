import dataclasses
import re
import shutil
from pathlib import Path

import pytest
import yaml
from perfrepair.dto.lifecycle import Step
from perfrepair.dto.site import SCOPES_SCHEMA_VERSION
from perfrepair.dto.unit import Link, Unit
from perfrepair.files import write_json
from perfrepair.scope.build import build_scopes
from perfrepair.scope.units.build import build_units
from perfrepair.validation.finding import BLOCKING, UNDECIDED
from perfrepair.validation.invariants import app_gate, run_invariants
from perfrepair.validation.scoping import invariants as inv
from perfrepair.validation.scoping.accuracy import link_accuracy, pattern_accuracy
from perfrepair.validation.scoping.source import Sources

F = Path(__file__).parent / "fixtures" / "scoping"
CALL = re.compile(r"(\w+)\.getInstance\(\"([^\"]*)\"\)")
EXPECTED = yaml.safe_load((F / "expected.yaml").read_text())


def sites(file: str) -> dict[str, dict]:
    out = {}
    for n, text in enumerate((F / file).read_text().splitlines(), 1):
        marker = re.search(r"// site: (\w+)", text)
        if marker:
            m = CALL.search(text)
            out[marker.group(1)] = {"file": file, "line": n, "call": m.group(0), "engineType": m.group(1),
                                    "resolvedAlgorithm": m.group(2), "resolvedProvider": "P1", "resolution": "explicit"}
    return out


@pytest.fixture(scope="module")
def read(tmp_path_factory):
    pytest.importorskip("tree_sitter_java")
    pytest.importorskip("tree_sitter_kotlin")
    root = tmp_path_factory.mktemp("app")
    found = {}
    for file in ("Ledger.java", "Notary.kt"):
        shutil.copy(F / file, root / file)
        found |= sites(file)
    scopes = build_scopes("demo", root, list(found.values())).scopes
    at = {(s.file, s.line): s for s in scopes}
    by_marker = {m: at.get((site["file"], site["line"])) for m, site in found.items()}
    return by_marker, build_units("demo", scopes, root), Sources(root)


def test_accuracy_per_rule_over_the_known_answers(read, capsys):
    by_marker, units, _ = read
    patterns = pattern_accuracy(EXPECTED["sites"], by_marker)
    links = link_accuracy(EXPECTED["links"], by_marker, units)
    with capsys.disabled():
        print("\n" + "\n".join(t.line(n) for n, t in {**patterns, **links}.items()))
    # the scoper's wrong readings today, recorded as findings: a change to the scoper changes this list
    wrong = sorted(w.split(",")[0] for t in {**patterns, **links}.values() for w in t.wrong)
    assert wrong == sorted(SCOPER_WRONG)


# the scoper's wrong readings of these sources today; each is a finding, not a target to tune to
SCOPER_WRONG = [
    "j_lazy read unknown_default (notFixed)", "k_lazy_null read created_per_call (notFixed)", "k_lazy_delegate read unscoped",
    "j_reinit read held_in_field (fixed)", "k_reinit read unscoped",
    # the parameter rule: an encrypt and a decrypt taking keys from callers in one class, whether or not they pair
    "extra k_apply k_escape", "extra k_escape k_local",
]


def test_the_invariants_on_the_known_answers(read, capsys):
    by_marker, units, sources = read
    found = inv.scoping_invariants([s for s in by_marker.values() if s], units, sources, INIT_PER_CALL)
    marker = {s.id: m for m, s in by_marker.items() if s}
    with capsys.disabled():
        print("\n" + "\n".join(f"{v.severity} {v.invariant} {marker.get(v.subject.split()[-1], v.subject)}" for v in found))
    flagged = {marker.get(v.subject.split()[-1]) for v in found if v.severity == BLOCKING}
    assert flagged == EXPECTED_FLAGGED


# held_in_field_setup_once catches the re-init of an item whose fixed variant does not init per call;
# j_fresh's does, and the lazy caches and the parameter links pass every source rule
EXPECTED_FLAGGED = {"j_reinit"}


def scope(line, reason, *steps, call='Cipher.getInstance("ALG-A/X")', engine="Cipher"):
    from perfrepair.dto.lifecycle import Lifecycle
    from perfrepair.dto.site import Scope
    lc = Lifecycle("bounded", (), "local", tuple(Step(r, c, n, w) for r, c, n, w in steps))
    return Scope(f"s{line}", "demo", "Ledger.java", line, call, "f", 1, 200, engine, "ALG", "P1", "explicit",
                 lifecycle=lc, patternReason=reason, pattern="notFixed")


SRC = Sources(F)
INIT_PER_CALL = frozenset({("Cipher", "ALG-C/Z")})
LOCAL = scope(59, "created_per_call", ("configure", "init", 60, "same"), ("use", "doFinal", 61, "same"))


def test_the_cited_line_must_start_the_call():
    assert inv.site_line_holds_call(LOCAL, SRC.code("Ledger.java")) == []
    moved = dataclasses.replace(LOCAL, line=60)
    found = inv.site_line_holds_call(moved, SRC.code("Ledger.java"))
    assert [(v.invariant, v.severity, v.evidence[0]) for v in found] == [("site_line_holds_call", BLOCKING, "Ledger.java:60")]


def test_created_per_call_needs_a_use_in_the_creating_function_on_a_line_that_holds_it():
    assert inv.created_per_call_one_function(LOCAL, SRC.code("Ledger.java")) == []
    elsewhere = scope(59, "created_per_call", ("use", "doFinal", 114, "depth1"))
    found = inv.created_per_call_one_function(elsewhere, SRC.code("Ledger.java"))
    assert [v.severity for v in found] == [BLOCKING] and "no use inside once" in found[0].evidence[1]
    off = scope(59, "created_per_call", ("use", "doFinal", 60, "same"))
    assert any("line holds no doFinal" in v.evidence[1] for v in inv.created_per_call_one_function(off, SRC.code("Ledger.java")))


def test_held_in_field_refuses_setup_in_the_using_method_and_says_when_it_cannot_tell():
    held = scope(13, "held_in_field", ("configure", "init", 14, "same"), ("use", "doFinal", 18, "depth1"), call='Mac.getInstance("ALG-M")', engine="Mac")
    assert inv.held_in_field_setup_once(held, SRC.code("Ledger.java")) == []
    reinit = scope(28, "held_in_field", ("configure", "init", 32, "depth1"), ("use", "doFinal", 33, "depth1"))
    found = inv.held_in_field_setup_once(reinit, SRC.code("Ledger.java"))
    assert [v.severity for v in found] == [BLOCKING] and "held.init" in found[0].evidence[1]
    blind = scope(28, "held_in_field", ("use", "doFinal", 31, "depth1"))
    assert [v.severity for v in inv.held_in_field_setup_once(blind, SRC.code("Ledger.java"))] == [UNDECIDED]


def test_an_inverse_link_between_two_encrypting_sides_blocks():
    a = scope(112, "created_per_call", ("configure", "init", 113, "same"), ("use", "doFinal", 114, "same"), call='Cipher.getInstance("ALG-B/Y")')
    b = scope(118, "created_per_call", ("configure", "init", 119, "same"), ("use", "doFinal", 120, "same"), call='Cipher.getInstance("ALG-B/Y")')
    unit = Unit("u1", (a.id, b.id), (Link("inverse", a.id, b.id, (113,), (119,), "key"),))
    found = inv.inverse_link_sides(unit, {a.id: a, b.id: b}, SRC)
    assert [(v.invariant, v.severity) for v in found] == [("inverse_link_sides", BLOCKING)] and "['ENCRYPT']" in found[0].evidence[0]
    assert [v.severity for v in inv.inverse_link_sides(unit, {a.id: a, b.id: b}, Sources(None))] == [UNDECIDED]


def test_no_source_is_undecided_never_a_guess():
    assert [(v.invariant, v.severity) for v in inv.scoping_invariants([LOCAL], [], Sources(None))] == [("site_line_holds_call", UNDECIDED)]


def fresh(class_name="FreshIv"):
    lines = (F / "Ledger.java").read_text().splitlines()
    start = lines.index(f"class {class_name} {{")
    site = next(n for n, text in enumerate(lines[start:], start + 1) if "Cipher.getInstance" in text)
    use = next(n for n, text in enumerate(lines[start:], start + 1) if "stream.doFinal" in text)
    return scope(site, "held_in_field", ("configure", "init", use - 1, "depth1"), ("use", "doFinal", use, "depth1"),
                 call='Cipher.getInstance("ALG-C/Z")')


def device_with(tmp_path, s, per_call):
    app = tmp_path / "device" / "demo"
    app.mkdir(parents=True)
    write_json(app / "app.json", {"root": str(F), "projectRoot": "."})
    doc = {"schemaVersion": SCOPES_SCHEMA_VERSION, "app": "demo", "scopes": [dataclasses.replace(s, algorithm="ALG-C/Z").to_json()]}
    write_json(app / "scopes.json", doc)
    row = {"type": "Cipher", "algorithm": "ALG-C/Z", "provider": "P1", "variant": "fixed", "perCall": per_call}
    write_json(tmp_path / "device" / "rows.json", {"schemaVersion": 2, "rows": [row]})
    return tmp_path / "device"


def test_a_re_init_is_accepted_when_the_fixed_variant_of_that_item_inits_per_call(tmp_path):
    device = device_with(tmp_path, fresh(), "initAndOperation")
    assert [v for v in run_invariants(device) if v.invariant == "held_in_field_setup_once"] == []
    assert [v for v in app_gate(device, "demo", F) if v.invariant == "held_in_field_setup_once"] == []


def test_a_re_init_still_blocks_when_the_fixed_variant_does_not_init_per_call(tmp_path):
    found = run_invariants(device_with(tmp_path, fresh(), "operation"))
    assert [(v.invariant, v.severity) for v in found] == [("held_in_field_setup_once", BLOCKING)]
    assert "stream.init" in found[0].evidence[1]


def test_a_factory_call_in_the_using_method_blocks_even_when_the_fixed_variant_inits_per_call():
    rebuilt = dataclasses.replace(fresh(class_name="Rebuilt"), algorithm="ALG-C/Z")
    found = inv.held_in_field_setup_once(rebuilt, SRC.code("Ledger.java"), INIT_PER_CALL)
    assert [v.severity for v in found] == [BLOCKING]
    assert "Cipher.getInstance" in found[0].evidence[1] and "stream.init" not in found[0].evidence[1]


def test_the_app_gate_reads_the_source_from_the_root_the_guide_passes(tmp_path):
    device = device_with(tmp_path, fresh(), "operation")
    write_json(device / "demo" / "app.json", {"root": str(tmp_path / "moved"), "projectRoot": "."})
    assert [v.severity for v in run_invariants(device)] == [UNDECIDED]
    assert [(v.invariant, v.severity) for v in app_gate(device, "demo", F)] == [("held_in_field_setup_once", BLOCKING)]
