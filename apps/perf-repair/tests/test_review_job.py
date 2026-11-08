"""Review after Select on a scripted transport: off by default, only on a pick that edits code; a refusal feeds Select's
repass, unidentified is a person's, reads by tool."""
import json
from pathlib import Path

from helpers import LIBRARY, QUIET, logged
from select_data import APP, doc, dossier
from test_select import A, run_dir

from perfrepair.ai.model.tier import Ladder, Tier
from perfrepair.ai.runtime.agent import ScriptedConversations
from perfrepair.ai.runtime.gateway.spawn import Spawned
from perfrepair.ai.select.command import select_units
from perfrepair.config.load import load
from perfrepair.dto.change import PairDiff
from perfrepair.dto.dossier import Estimate, Option
from perfrepair.files import read_json
from perfrepair.inputs.table import APPS_REVIEW

EXAMPLE = Path(__file__).parents[1] / "perfrepair.example.yaml"
ACCEPT = lambda *_: {"tool": "verdict", "args": {"verdict": "accept", "reason": "ok"}}


def tiered(select, review):
    """The select tier answers by `select`, the one above it by `review`."""
    def at(tier):
        return ScriptedConversations(select if tier.model == "small" else review)
    tier = Tier("scripted", "small", "low")
    return Spawned(at(tier), tier, None, at, Ladder(("small", "big")))


def test_a_refused_review_is_the_next_repass_reason_and_the_reviewers_tier_is_one_up(tmp_path):
    run, app = run_dir(tmp_path, A)
    seen = []

    def select(task, *_):
        seen.append(task.text)
        return {"tool": "submit", "args": {"option": "C2" if "EARLIER ATTEMPTS" in task.text else "C1", "reason": "fast"}}
    verdicts = iter(["refuse", "accept"])

    def review(task, *_):
        return {"tool": "verdict", "args": {"verdict": next(verdicts), "reason": "C2 is measured nearer this input size"}}
    select_units(run, APP, tiered(select, review), LIBRARY, review=True, **QUIET)
    first, second = logged(run, "select")
    assert first["outcome"] == "refused" and first["reason"] == {"source": "review", "problems": ["C2 is measured nearer this input size"]}
    assert "attempt 1 was refused: review: C2 is measured nearer this input size" in seen[1]
    assert second["outcome"] == "decided" and second["review"]["verdict"] == "accept"
    assert [e["tier"]["model"] for e in logged(run, "review")] == ["big", "big"]
    [row] = read_json(app / "replacements.json")["replacements"]
    assert row["option"] == "TypeA|ALG-A/MODE-X|P3"


def test_unidentified_leaves_the_item_to_a_person(tmp_path):
    run, app = run_dir(tmp_path, A)
    select = lambda *_: {"tool": "submit", "args": {"option": "C1", "reason": "fast"}}
    review = lambda *_: {"tool": "verdict", "args": {"verdict": "unidentified", "reason": "the sink is not visible here"}}
    select_units(run, APP, tiered(select, review), LIBRARY, review=True, **QUIET)
    [row] = read_json(app / "replacements.json")["replacements"]
    assert (row["decision"], row["reason"]) == ("keep", "review: the sink is not visible here")
    assert read_json(app / "replacements.json")["sources"] == {A.key: "fallback"}


def test_the_reviewer_reads_the_answer_and_evidence_through_its_tools(tmp_path):
    run, app = run_dir(tmp_path, A)
    reads = iter([{"tool": "read_output", "args": {}}, {"tool": "read_evidence", "args": {}},
                  {"tool": "verdict", "args": {"verdict": "accept", "reason": "ok"}}])
    select = lambda *_: {"tool": "submit", "args": {"option": "C1", "reason": "fast"}}
    select_units(run, APP, tiered(select, lambda *_: next(reads)), LIBRARY, review=True, **QUIET)
    [entry] = logged(run, "review")
    assert [c["tool"] for c in entry["calls"]] == ["read_output", "read_evidence", "verdict"]
    assert entry["item"].startswith("select:") and entry["label"].startswith("select src/Box.kt")
    assert read_json(app / "replacements.json")["replacements"][0]["decision"] == "replace"



def test_review_is_off_unless_the_settings_turn_it_on(tmp_path):
    config = tmp_path / "c.yaml"
    for text, on in (("", False), ("apps: {review: true}\n", True)):
        config.write_text(text)
        assert load(config, {}, {}).read(APPS_REVIEW) is on
    assert load(EXAMPLE, {}, {}).read(APPS_REVIEW) is False


def test_a_pick_that_edits_code_is_reviewed(tmp_path):
    run, app = run_dir(tmp_path, A)
    select_units(run, APP, tiered(lambda *_: {"tool": "submit", "args": {"option": "C1", "reason": "fast"}}, ACCEPT), LIBRARY,
                 review=True, **QUIET)
    assert len(logged(run, "review")) == 1 and read_json(app / "replacements.json")["replacements"][0]["edits"]


def test_none_is_never_reviewed(tmp_path):
    run, app = run_dir(tmp_path, A)
    select_units(run, APP, tiered(lambda *_: {"tool": "submit", "args": {"option": "none", "reason": "unsure"}}, ACCEPT),
                 LIBRARY, review=True, **QUIET)
    [entry] = logged(run, "select")
    assert entry["outcome"] == "decided" and "review" not in entry and logged(run, "review") == []
    assert read_json(app / "replacements.json")["replacements"][0]["decision"] == "keep"


def test_a_recommendation_edits_no_code_and_is_not_reviewed(tmp_path):
    leaves = dossier(options=(Option("R1", "TypeA|X|P2", {}, "pass", (Estimate("timeNs", 0.6, 0.99, 9, "c"),), change="local-edit",
                                     diff=PairDiff("same", "same", "bytes", "persist"), outputChanges=True),))
    run, app = run_dir(tmp_path)
    (app / "dossiers.json").write_text(json.dumps(doc(leaves, max_change="local-edit")))
    select_units(run, APP, tiered(lambda *_: {"tool": "submit", "args": {"option": "C1", "reason": "fast"}}, ACCEPT), LIBRARY,
                 review=True, **QUIET)
    [row] = read_json(app / "replacements.json")["replacements"]
    assert (row["decision"], row["edits"]) == ("recommend", []) and logged(run, "review") == []
