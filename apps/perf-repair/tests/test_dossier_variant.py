"""A scope's estimates, MEASURED lines and perCall come from its pattern's benchmark variant only."""
from dataclasses import replace

from helpers import TIMING, summary
from test_dossier import GROUPS, M, ROWS, build, scope

from perfrepair.ai.select.units import evidence
from perfrepair.ai.select.render import pattern_line
from perfrepair.ai.select.rows import lines_of
from perfrepair.dto.lifecycle import Lifecycle, Step
from perfrepair.dto.dossier import Dossier
from perfrepair.dto.unit import Unit, UnitDossiers, unit_id
from perfrepair.result.primitives import build_table
from perfrepair.validation.dossiers.against_run import validate_dossiers

# the fixed variant: the option halves the time, where notFixed shows 0.8
FIXED = [replace(r, rowId=f"{r.rowId}_fixed", variant="fixed", perCall="operation") for r in ROWS]
NOT_FIXED = [replace(r, rowId=f"{r.rowId}_notFixed", perCall="getInstanceInitAndOperation") for r in ROWS]
BOTH = FIXED + NOT_FIXED
MB = {**{f"{k}_notFixed": v for k, v in M.items()}, **{f"{k}_fixed": v for k, v in M.items()},
      "o64_fixed": {"timeNs": summary(50), "allocationCount": summary(12)}}
HELD = Lifecycle("partially_bounded", ("field", "depth1"), "field", (Step("use", "f", 3, "depth1"),))


def fixed_scope():
    return replace(scope(), lifecycle=HELD, pattern="fixed", patternReason="held_in_field", patternLines=(2, 3))


def _time(doc) -> tuple[float, str]:
    d = Dossier.from_json(doc["dossiers"][0])
    e = next(e for e in d.options[0].estimates if e.metric == "timeNs")
    return e.ratio, d.perCall


def test_each_scope_reads_only_its_patterns_variant(tmp_path):
    assert _time(build([scope()], tmp_path, rows=BOTH, measurements=MB)) == (0.8, ("getInstanceInitAndOperation",))
    assert _time(build([fixed_scope()], tmp_path, rows=BOTH, measurements=MB)) == (0.5, ("operation",))


def test_a_scope_whose_variant_was_not_measured_has_no_options_with_the_reason(tmp_path):
    doc = build([fixed_scope()], tmp_path)
    assert doc["dossiers"] == [] and doc["noOptions"] == [{"scope": fixed_scope().id, "reason": "variant_not_measured"}]
    assert validate_dossiers(doc, [fixed_scope()], GROUPS, None) == []


def test_the_render_names_the_category_and_the_measured_lines_are_its_variant(tmp_path):
    d = Dossier.from_json(build([fixed_scope()], tmp_path, rows=BOTH, measurements=MB)["dossiers"][0])
    assert pattern_line(d) == ("  pattern: fixed (held_in_field: a field holds the object, created outside the methods that "
                               "use it one method away); the estimates and measured lines are the fixed variant's, its "
                               "timed call redoing operation")
    status = {q["qualified"]: "accepted" for q in GROUPS["items"].values()}
    table = build_table(BOTH, {k: {m: v for m, v in by.items() if v is not None} for k, by in MB.items()}, status)
    assert {line.variant for _, line in lines_of(d, table)} == {"fixed"}


def test_the_evidence_digest_changes_with_the_pattern(tmp_path):
    d = Dossier.from_json(build([scope()], tmp_path, rows=BOTH, measurements=MB, perf=TIMING)["dossiers"][0])
    flipped = replace(d, scope=replace(d.scope, pattern="fixed", patternReason="held_in_field"))
    unit = Unit(unit_id("app", [d.key]), (d.key,))
    assert evidence(UnitDossiers(unit, (d,)), TIMING) != evidence(UnitDossiers(unit, (flipped,)), TIMING)
