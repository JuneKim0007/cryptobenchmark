import dataclasses
import re
import shutil
from pathlib import Path

import pytest
import yaml
from perfrepair.dto.lifecycle import Step
from perfrepair.dto.unit import Link, Unit
from perfrepair.scope.build import build_scopes
from perfrepair.scope.units.build import build_units
from perfrepair.validation.finding import BLOCKING, UNDECIDED
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
    found = inv.scoping_invariants([s for s in by_marker.values() if s], units, sources)
    marker = {s.id: m for m, s in by_marker.items() if s}
    with capsys.disabled():
        print("\n" + "\n".join(f"{v.severity} {v.invariant} {marker.get(v.subject.split()[-1], v.subject)}" for v in found))
    flagged = {marker.get(v.subject.split()[-1]) for v in found if v.severity == BLOCKING}
    assert flagged == EXPECTED_FLAGGED


# held_in_field_setup_once catches the re-init; the lazy caches and the parameter links pass every source rule
EXPECTED_FLAGGED = {"j_reinit"}


def scope(line, reason, *steps, call='Cipher.getInstance("ALG-A/X")', engine="Cipher"):
    from perfrepair.dto.lifecycle import Lifecycle
    from perfrepair.dto.site import Scope
    lc = Lifecycle("bounded", (), "local", tuple(Step(r, c, n, w) for r, c, n, w in steps))
    return Scope(f"s{line}", "demo", "Ledger.java", line, call, "f", 1, 200, engine, "ALG", "P1", "explicit",
                 lifecycle=lc, patternReason=reason, pattern="notFixed")


SRC = Sources(F)
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
