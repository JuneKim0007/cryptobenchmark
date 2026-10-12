import json
import re

from conftest import QUIET, Remembering, by_name
from grouping_data import FAMILIES

from perfrepair.grouping.kind import GroupingKind
from perfrepair.orchestrate.engine.ask import Limits
from perfrepair.orchestrate.engine.decide import decide
from perfrepair.grouping.report.checks import report
from perfrepair.grouping.supervise.run import supervise
from perfrepair.orchestrate.agent import ScriptedConversations
from perfrepair.validation.grouping.supervision import parse_review


def finished(paths):
    decide(GroupingKind(paths, FAMILIES), ScriptedConversations(by_name), paths.root, **QUIET)
    report(paths, FAMILIES)
    return json.loads(paths.groups.read_text())


def groups_in(message):
    return re.findall(r"^GROUP (\S+)", message, re.M)


def test_a_sound_grouping_reviews_clean_and_the_grouping_is_untouched(paths):
    before = finished(paths)
    out = supervise(paths, ScriptedConversations(lambda *_: {"findings": []}), **QUIET)
    assert {f["status"] for f in out["families"].values()} == {"reviewed"}
    assert json.loads(paths.groups.read_text()) == before
    assert json.loads(paths.supervisor.read_text()) == out


def test_findings_are_kept_and_out_of_family_ones_corrected(paths):
    finished(paths)

    def review(message, conversation, turn):
        names = groups_in(message)
        if len(names) < 2:
            return {"findings": []}
        if turn == 1:
            return {"findings": [{"kind": "merge", "groups": [names[0], "elsewhere"], "items": [], "reason": "x"}]}
        return {"findings": [{"kind": "merge", "groups": names[:2], "items": [], "reason": "same function"}]}
    out = supervise(paths, ScriptedConversations(Remembering(review)), **QUIET)
    secret = out["families"]["cipher.secret"]
    assert secret["status"] == "reviewed" and secret["findings"][0]["kind"] == "merge"
    log = [json.loads(line) for line in paths.supervisor_journal.read_text().splitlines()]
    assert any("'elsewhere' is not in this family" in p for line in log for p in line["problems"])


def test_a_review_no_conversation_completes_is_marked_failed(paths):
    finished(paths)
    out = supervise(paths, ScriptedConversations(lambda *_: "not json"), Limits(turns=1, sessions=2), **QUIET)
    assert all(f["status"] == "failed" and len(f["problems"]) == 2 for f in out["families"].values())


def test_parse_review_checks_arity_per_kind():
    groups = {"a": [1], "b": [2]}
    _, problems = parse_review(json.dumps({"findings": [
        {"kind": "merge", "groups": ["a"], "items": [], "reason": "r"},
        {"kind": "split", "groups": ["a", "b"], "items": [1], "reason": "r"},
        {"kind": "misplaced", "groups": ["a"], "items": [9], "reason": ""},
        {"kind": "rename", "groups": [], "items": [], "reason": "r"}]}), groups)
    for expected in ("fewer than two groups", "split names exactly one group", "item 9 is not in this family",
                     "misplaced names the item", "reason is empty", "'rename' is not one of"):
        assert any(expected in p for p in problems), expected
