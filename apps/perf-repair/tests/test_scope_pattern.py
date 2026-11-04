from pathlib import Path

import pytest

from perfrepair.dto.lifecycle import Lifecycle, Step
from perfrepair.dto.pattern import PATTERN_RULES
from perfrepair.scope.pattern import pattern_of

F = Path(__file__).parent / "fixtures" / "lifecycle"


def lc(status, reasons, binding, *steps) -> Lifecycle:
    return Lifecycle(status, reasons, binding, tuple(Step(role, "f", line, where) for role, line, where in steps))


@pytest.mark.parametrize("lifecycle, pattern, reason, lines", [
    (lc("bounded", (), "local", ("configure", 11, "same"), ("use", 12, "same")), "notFixed", "created_per_call", (10, 11, 12)),
    (lc("bounded", (), "chain", ("use", 10, "same")), "notFixed", "created_per_call", (10,)),
    (lc("partially_bounded", ("wrapper",), "local", ("consume", 12, "same")), "notFixed", "created_per_call", (10, 12)),
    (lc("partially_bounded", ("field", "depth1"), "field", ("configure", 11, "same"), ("use", 30, "depth1")),
     "fixed", "held_in_field", (10, 11, 30)),
    # a field used beside its creation: a lazy cache or a re-creation, the reading cannot tell
    (lc("partially_bounded", ("field", "depth1"), "field", ("use", 12, "same"), ("use", 30, "depth1")),
     "notFixed", "unknown_default", (10, 12, 30)),
    (lc("partially_bounded", ("escape", "depth1"), "returned", ("use", 30, "depth1")), "notFixed", "unknown_default", (10, 30)),
    (lc("partially_bounded", ("deferred",), "local", ("use", 12, "same")), "notFixed", "unknown_default", (10, 12)),
    (lc("partially_bounded", ("field", "budget"), "field", ("use", 30, "depth1")), "notFixed", "unknown_default", (10, 30)),
    (lc("partially_bounded", ("use_not_found",), "local", ("configure", 11, "same")), "notFixed", "unknown_default", (10, 11)),
    (lc("no_real_use", (), "discarded"), "notFixed", "unknown_default", (10,)),
    (Lifecycle.unsupported("parser_missing"), "notFixed", "unknown_default", (10,)),
    (None, "notFixed", "unknown_default", (10,)),
])
def test_each_rule_gives_its_category_reason_and_evidence_lines(lifecycle, pattern, reason, lines):
    assert tuple(pattern_of(lifecycle, 10)) == (pattern, reason, lines)


def test_every_reason_names_its_category_and_a_rule():
    assert {p for p, _ in PATTERN_RULES.values()} == {"fixed", "notFixed"}
    assert all(words for _, words in PATTERN_RULES.values())


@pytest.mark.parametrize("file, marker, pattern, reason", [
    ("Box.java", "local", "notFixed", "created_per_call"),
    ("Box.java", "chain", "notFixed", "created_per_call"),
    ("Box.java", "wrapper", "notFixed", "created_per_call"),
    ("Box.java", "field", "fixed", "held_in_field"),
    ("Box.java", "returned", "notFixed", "unknown_default"),
    ("Box.java", "argument", "notFixed", "unknown_default"),
    ("Box.java", "no_real_use", "notFixed", "unknown_default"),
    ("Seal.kt", "lazy_field", "fixed", "held_in_field"),
    ("Seal.kt", "apply", "notFixed", "created_per_call"),
    ("Seal.kt", "with", "notFixed", "created_per_call"),
    ("Seal.kt", "deferred", "notFixed", "unknown_default"),
])
def test_the_rule_over_read_sources(file, marker, pattern, reason):
    pytest.importorskip("tree_sitter_java")
    pytest.importorskip("tree_sitter_kotlin")
    from test_lifecycle import read
    text = (F / file).read_text()
    line = next(n for n, t in enumerate(text.splitlines(), 1) if t.rstrip().endswith(f"// site: {marker}"))
    assert pattern_of(read(file, marker), line)[:2] == (pattern, reason)
