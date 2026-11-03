import re
from pathlib import Path

import pytest

from perfrepair.scope.engines import read_engines
from perfrepair.source.language import of_file

pytest.importorskip("tree_sitter")
pytest.importorskip("tree_sitter_java")
pytest.importorskip("tree_sitter_kotlin")

from perfrepair.scope.lifecycle.candidates import REACH_LINES  # noqa: E402
from perfrepair.scope.lifecycle.gaps import Found, Where, gaps_of  # noqa: E402
from perfrepair.scope.lifecycle.read import read_site  # noqa: E402
from perfrepair.scope.syntax.parser import parse  # noqa: E402

F = Path(__file__).parent / "fixtures" / "lifecycle"
CALL = re.compile(r"(\w+)\.getInstance\(\"[^\"]*\"\)")


def found(file: str, marker: str) -> Found:
    text = (F / file).read_text()
    lines = text.splitlines()
    n = next(i for i, t in enumerate(lines, 1) if t.rstrip().endswith(f"// site: {marker}"))
    m = CALL.search(lines[n - 1])
    reading = read_site(parse(text, of_file(file)), {"line": n, "call": m.group(0), "engineType": m.group(1)}, read_engines())
    return gaps_of(reading, read_engines(), Where("sid", file, "fn", n, lines))


def only_gap(file, marker, name="key"):
    return next(g for g in found(file, marker).gaps.gaps if g.name == name)


def test_a_fields_writes_are_its_candidates_and_a_writer_body_is_the_one_other_body():
    gap = only_gap("Vault.java", "field_key")
    assert [(c.how, c.reads) for c in gap.candidates] == [("field_write", "parameter"), ("field_write", "other_call")]
    assert gap.candidates[0].text == "held = given;"
    assert found("Vault.java", "field_key").gaps.body.lines[0].strip().startswith("Vault(Key given)")


def test_a_private_helper_that_returns_one_closed_origin_is_settled_by_code_and_never_asked():
    f = found("Vault.java", "call_key")
    done = next(iter(f.settled.values()))
    assert (done.origin, done.source) == ("keystore", "code") and f.gaps is None


def test_a_helper_returning_an_open_call_is_a_gap_with_its_return_line():
    assert [(c.how, c.reads) for c in only_gap("Vault.java", "opaque_key").candidates] == [("returned", "other_call")]
    assert [(c.how, c.reads) for c in only_gap("Ledger.kt", "returned_open").candidates] == [("returned", "other_call")]


def test_a_kotlin_expression_body_returns_its_expression():
    assert next(iter(found("Ledger.kt", "expression_body").settled.values())).origin == "literal"


def test_a_public_parameter_is_never_settled_by_its_callers_in_the_class():
    f = found("Vault.java", "public_key")
    assert f.settled == {} and [c.reads for c in f.gaps.gaps[0].candidates] == ["keystore"]


def test_a_gap_no_line_reaches_is_recorded_and_not_offered():
    gaps = found("Vault.java", "no_caller").gaps
    assert gaps.gaps[0].candidates == () and gaps.offered == ()


def test_a_closed_origin_is_no_gap():
    assert found("Vault.java", "closed").gaps is None


def test_the_budget_caps_the_lines_and_says_so():
    gap = only_gap("Vault.java", "over_budget")
    assert len(gap.candidates) == REACH_LINES and gap.over_budget


def test_an_arrays_size_is_not_its_value():
    f = found("Vault.java", "array_size")
    assert f.settled == {} and only_gap("Vault.java", "array_size", "parameters").candidates == ()


def test_a_branch_offers_its_operands():
    assert {c.how for c in only_gap("Vault.java", "branch").candidates} >= {"part"}


def test_a_lost_use_offers_the_references_and_the_helpers_callers():
    gap = only_gap("Vault.java", "lost_use", "use")
    assert {c.how for c in gap.candidates} == {"object_reference", "helper_caller"}
    assert "keep(lost());" in [c.text for c in gap.candidates]
