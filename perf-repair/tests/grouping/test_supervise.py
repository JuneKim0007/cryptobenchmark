import json
import re

from conftest import CHARTER, LIBRARY, QUIET, by_name
from grouping_data import FAMILIES

from perfrepair.ai.parse.grouping_assign.kind import GroupingKind
from perfrepair.ai.runtime.engine.ask import Limits
from perfrepair.ai.runtime.engine.decide import decide
from perfrepair.grouping.report.checks import report
from perfrepair.ai.review.grouping_review.run import charter as supervisor_charter, supervise
from perfrepair.ai.runtime.agent import ScriptedConversations
from perfrepair.ai.runtime.prompt import PromptLibrary
from perfrepair.validation.review.grouping_review import parse_review


def finished(paths):
    decide(GroupingKind(paths, FAMILIES), CHARTER, ScriptedConversations(by_name), paths.root, **QUIET)
    report(paths, FAMILIES)
    return json.loads(paths.groups.read_text())


def review(paths, answer, *args, library=LIBRARY):
    used = supervisor_charter(library)
    return supervise(paths, used, ScriptedConversations(answer), library.provenance(used), *args, **QUIET)


def groups_in(task):
    return re.findall(r"^GROUP (\S+)", task.text, re.M)


def test_a_sound_grouping_reviews_clean_and_the_grouping_is_untouched(paths):
    before = finished(paths)
    out = review(paths, lambda *_: {"findings": []})
    assert {f["status"] for f in out["families"].values()} == {"reviewed"}
    assert json.loads(paths.groups.read_text()) == before
    assert json.loads(paths.supervisor.read_text()) == out


def test_the_review_is_one_model_step_with_a_turn_and_a_decision_per_family(paths, tmp_path):
    from perfrepair.log import attach
    from perfrepair.log.read import read_events
    finished(paths)
    attach()
    attach(tmp_path)
    out = review(paths, lambda *_: {"findings": []})
    events = [e for e in read_events(tmp_path / "log" / "events.jsonl") if e.step == "review"]
    assert events[0].event == "start" and events[0].data["pending"] == len(out["families"])
    assert [e.item for e in events if e.event == "decision"] == sorted(out["families"])
    assert events[-1].event == "end" and events[-1].data["counts"] == {"reviewed": len(out["families"])}
    assert all(e.ref.split(":")[0].endswith("supervisor.journal.jsonl") for e in events if e.event == "turn")


def test_supervisor_json_records_an_override_source_and_its_own_charter(paths, tmp_path):
    finished(paths)
    packaged = review(paths, lambda *_: {"findings": []})
    override = tmp_path / "prompts" / "review" / "grouping-review.system.md"
    override.parent.mkdir(parents=True)
    override.write_text("REVIEW OVERRIDE")
    out = review(paths, lambda *_: {"findings": []}, library=PromptLibrary.load(override.parents[1]))
    assert out["prompts"]["review/grouping-review"] == str(override)
    assert out["prompts"]["shared/rejection"] == packaged["prompts"]["shared/rejection"]
    assert out["charter"] != packaged["charter"]
    journal = [json.loads(line) for line in paths.supervisor_journal.read_text().splitlines()]
    assert {line["charter"] for line in journal} == {packaged["charter"], out["charter"]}
    charter = json.loads(paths.supervisor_charter.read_text())
    assert charter["fingerprint"] == out["charter"] and charter["system"]["source"] == str(override)
    assert charter["system"]["text"] == "REVIEW OVERRIDE" and charter["correction"]["source"] == "packaged"


def test_findings_are_kept_and_out_of_family_ones_corrected(paths):
    finished(paths)

    def answer(message, conversation, turn):
        names = groups_in(message)
        if len(names) < 2:
            return {"findings": []}
        if turn == 1:
            return {"findings": [{"kind": "merge", "groups": [names[0], "elsewhere"], "items": [], "reason": "x"}]}
        return {"findings": [{"kind": "merge", "groups": names[:2], "items": [], "reason": "same function"}]}
    out = review(paths, answer)
    secret = out["families"]["cipher.secret"]
    assert secret["status"] == "reviewed" and secret["findings"][0]["kind"] == "merge"
    log = [json.loads(line) for line in paths.supervisor_journal.read_text().splitlines()]
    assert any("'elsewhere' is not in this family" in p for line in log for p in line["problems"])


def test_a_review_no_conversation_completes_is_marked_failed(paths):
    finished(paths)
    out = review(paths, lambda *_: "not json", Limits(turns=1, sessions=2))
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
