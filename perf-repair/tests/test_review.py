"""The accuracy sheet and its score over a small device folder written the way the engine writes it."""
import csv
import json

import pytest

from perfrepair import run_dir as rd
from perfrepair.dto.change import PairDiff
from perfrepair.dto.decision import AgentIdentity, OutboxRecord
from perfrepair.dto.grouping import Item, Profile, items_document, profiles_document
from perfrepair.dto.signature import Component, Signature
from perfrepair.dto.site import DOSSIERS_SCHEMA_VERSION, Dossier, Option, Scope, scope_id
from perfrepair.review.__main__ import main
from perfrepair.review.score import score
from perfrepair.review.sheet import COLUMNS, read_sheet, write_sheet

FP = "aaaaaaaaaaaa"
AGENT = AgentIdentity("g", "m", "low")
ITEM = Item(1, "TypeA", "ALG", "P1", "fam")
SCOPE = Scope(scope_id("app", "A.java", "f", 2, "c"), "app", "A.java", 2, "c", "f", 1, 3, "TypeA", "ALG", "P1", "explicit", None, None, ("local",))
OPTION = "TypeA|ALG-B|P1"


def _outbox(root, *records):
    folder = root / "outbox" / FP
    folder.mkdir(parents=True)
    (root / "outbox" / "active").write_text(FP)
    for r in records:
        (folder / f"{r.seq:06d}.json").write_text(json.dumps(r.to_json()))


def _turn(item, status="accepted", text="{}", sha="m1"):
    return {"charter": FP, "item": item, "session": 1, "turn": 1, "status": status, "problems": [],
            "reply": {"text": text}, "messageSha": sha, "durationMs": 1}


def _journal(root, *turns):
    (root / "journal.jsonl").write_text("".join(json.dumps(t) + "\n" for t in turns))


@pytest.fixture
def device(tmp_path):
    grouping = rd.GroupingPaths(tmp_path)
    grouping.root.mkdir()
    grouping.items.write_text(json.dumps(items_document([ITEM])))
    grouping.profiles.write_text(json.dumps(profiles_document(
        {1: Profile("none", "x", True, True, signature=Signature((Component("function", "ALG"),)))})))
    _outbox(grouping.root, OutboxRecord(1, ITEM.key, "decided", 1, 1, {"group": "g1", "newGroup": {"id": "", "description": ""}, "reason": "same"}, (), AGENT),
            OutboxRecord(2, "other", "dropped", 1, 3, None, ("no json",), AGENT))
    _journal(grouping.root, _turn(ITEM.key, text='{"group": "g1", "reason": "a"}'), _turn(ITEM.key, text='{"group": "g1", "reason": "b"}'),
             _turn("x", text='{"group": "g1"}', sha="m2"), _turn("x", text='{"group": "g2"}', sha="m2"), _turn("x", "rejected", sha="m2"))
    paths = rd.AppPaths(tmp_path, "app")
    paths.replace.mkdir(parents=True)
    paths.root.joinpath("app.json").write_text("{}")
    d = Dossier(SCOPE, "src", "TypeA|ALG|P1", (Option("R1", OPTION, {}, "not_planned", change="local-edit", diff=PairDiff("same", "same", "bytes", "local")),))
    paths.dossiers.write_text(json.dumps({"schemaVersion": DOSSIERS_SCHEMA_VERSION, "dossiers": [d.to_json()]}))
    row = {"scope": SCOPE.id, "decision": "replace", "option": OPTION, "edits": [], "risks": [], "reason": "faster"}
    _outbox(paths.replace, OutboxRecord(1, "unit", "decided", 1, 1, {"replacements": [row]}, (), AGENT))
    _journal(paths.replace, _turn("unit", text='{"decision": "replace"}', sha="m3"), _turn("unit", "rejected", sha="m3"))
    return tmp_path


def test_a_row_per_decision_with_code_facts_pick_reason_and_empty_verdict(device):
    rows = {(r["kind"], r["item"]): r for r in write_sheet(device)}
    # riskiest first: a replace before any other kind
    assert list(rows) == [("replace", SCOPE.id), ("grouping", ITEM.key), ("grouping", "other")]
    group = rows[("grouping", ITEM.key)]
    assert (group["pick"], group["reason"], group["verdict"], group["note"]) == ("g1", "same", "", "")
    assert json.loads(group["facts"]) == {"family": "fam", "signature": {"function": "ALG"}}
    swap = rows[("replace", SCOPE.id)]
    assert swap["app"] == "app" and swap["pick"] == f"replace {OPTION}"
    assert json.loads(swap["facts"])["change"] == "local-edit" and json.loads(swap["facts"])["sinks"] == ["local"]
    assert rows[("grouping", "other")]["pick"] == "(dropped)" and rows[("grouping", "other")]["reason"] == "no json"


def _fill(device, verdicts):
    path = rd.review_sheet(device)
    rows = read_sheet(path)
    for r in rows:
        r["verdict"], r["note"] = verdicts.get(r["kind"], ("", ""))
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, COLUMNS, delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def test_a_rebuild_keeps_what_a_person_filled_and_clears_a_changed_pick(device):
    write_sheet(device)
    _fill(device, {"grouping": ("ok", "looks right")})
    kept = {r["item"]: r for r in write_sheet(device)}
    assert (kept[ITEM.key]["verdict"], kept[ITEM.key]["note"]) == ("ok", "looks right")
    outbox = rd.GroupingPaths(device).root / "outbox" / FP / "000001.json"
    raw = json.loads(outbox.read_text())
    raw["decision"]["group"] = "g9"
    outbox.write_text(json.dumps(raw))
    assert {r["item"]: r["verdict"] for r in write_sheet(device)}[ITEM.key] == ""


def test_score_counts_only_judged_rows(device):
    write_sheet(device)
    assert score(device)["groupingPrecision"] == {"value": None, "right": 0, "judged": 0}
    _fill(device, {"grouping": ("ok", ""), "replace": ("wrong", "")})
    doc = score(device)
    assert doc["decisions"] == 3
    assert doc["groupingPrecision"]["value"] == 1.0 and doc["groupingPrecision"]["judged"] == 2
    assert doc["pickAccuracy"] == {"value": 0.0, "right": 0, "judged": 1}
    assert json.loads(rd.review_score(device).read_text()) == doc


def test_stability_compares_the_choice_not_the_words_on_one_message(device):
    write_sheet(device)
    assert score(device)["stability"] == {"value": 0.5, "right": 1, "judged": 2, "asks": 4}


def test_gate_rejections_per_100_calls(device):
    write_sheet(device)
    gate = score(device)["gateRejections"]
    assert (gate["calls"], gate["rejected"]) == (7, 2) and gate["per100"] == pytest.approx(200 / 7)
    assert gate["byKind"]["replace"]["per100"] == 50


def test_a_verdict_outside_the_vocabulary_is_refused(device):
    write_sheet(device)
    _fill(device, {"grouping": ("maybe", "")})
    with pytest.raises(ValueError, match="review_verdict"):
        score(device)


def test_the_command_writes_the_sheet_and_prints_the_score(device, capsys):
    assert main(["score", str(device)]) == 0
    assert json.loads(capsys.readouterr().out)["decisions"] == 3 and rd.review_sheet(device).is_file()


def test_stability_asks_each_sampled_unit_k_times_and_commits_nothing(tmp_path):
    from helpers import LIBRARY
    from site_replace_data import APP, KEEP, doc, dossier
    from perfrepair.ai.runtime.agent import ScriptedConversations
    from perfrepair.review.stability import stability
    app = tmp_path / APP
    app.mkdir()
    (app / "app.json").write_text(json.dumps({"root": str(tmp_path)}))
    (app / "dossiers.json").write_text(json.dumps(doc(dossier())))
    asked = ScriptedConversations(lambda *_: KEEP)
    out = stability(tmp_path, asked, LIBRARY, sample=5, asks=3)
    assert out["sample"] == 1 and out["stable"] == 1 and asked.started == 3 and not (app / "replace").exists()


def test_the_sheet_puts_the_riskiest_decisions_first():
    from perfrepair.review.sheet import risk
    rows = [{"kind": "grouping", "pick": "g"}, {"kind": "replace", "pick": "keep", "facts": "{}"},
            {"kind": "replace", "pick": "replace X", "facts": "{}"}, {"kind": "replace", "pick": "recommend Y", "facts": "{}"},
            {"kind": "replace", "pick": "replace Z", "facts": '{"label": "trade_off"}'}]
    assert [r["pick"] for r in sorted(rows, key=risk)] == ["recommend Y", "replace Z", "replace X", "keep", "g"]
