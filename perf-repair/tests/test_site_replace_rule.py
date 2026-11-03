"""The replacement gate's performance rule: listed perfModes strict, generic an overall judgement with named metrics;
recommend, concerns, and the prompts override folder's outbox."""
import json

from helpers import LIBRARY, QUIET
from site_replace_data import APP, KEEP, answer, dossier, doc, edit, item, member

from perfrepair.ai.runtime.agent import ScriptedConversations
from perfrepair.ai.runtime.engine.outbox import active_fingerprint
from perfrepair.ai.runtime.prompt import PromptLibrary
from perfrepair.ai.suggest.site_replace.command import replace
from perfrepair.dto.change import PairDiff
from perfrepair.dto.perf_mode import GENERIC_MODE, PerfMode
from perfrepair.dto.site import Estimate, Option
from perfrepair.files import read_json
from perfrepair.validation.suggest.site_replace import check_reply

AT = "OP1 key 128 input 1024"
FAST_HEAVY = Option("R1", "TypeA|ALG-A/MODE-X|P2", {"ivLength": 12, "tagMode": "full"}, "pass",
                    (Estimate("timeNs", 0.6, 0.99, 40, AT), Estimate("allocationCount", 1.5, 0.01, 40, AT)))
FLAT = Option("R1", "TypeA|ALG-A/MODE-X|P2", {"ivLength": 12, "tagMode": "full"}, "pass", (Estimate("timeNs", 0.99, 0.6, 40, AT),))
LISTED = PerfMode.parse(["latency", "memAlloc"])


def gate(option, reply, perf=GENERIC_MODE):
    return check_reply(json.dumps(reply), item(dossier(options=(option,))), perf=perf)


def test_generic_accepts_a_trade_off_naming_its_deciding_metric_and_its_accepted_loss():
    decision, problems = gate(FAST_HEAVY, answer(deciding=("timeNs",), accepted=("allocationCount",)))
    row = decision["replacements"][0]
    assert problems == [] and row["deciding"] == ["timeNs"] and row["accepted"] == ["allocationCount"]


def test_generic_refuses_a_trade_off_that_hides_its_loss_or_names_a_metric_that_did_not_improve():
    assert gate(FAST_HEAVY, answer(deciding=("timeNs",)))[1] == ["S1 R1 is worse on allocationCount; name it in accepted"]
    problems = gate(FAST_HEAVY, answer(deciding=("allocationCount",), accepted=("allocationCount",)))[1]
    assert problems == ["deciding metric allocationCount did not improve for S1 R1 (improved: timeNs)"]
    assert gate(FAST_HEAVY, answer(deciding=(), accepted=("allocationCount",)))[1] == ["a generic replace names its deciding metrics"]


def test_generic_refuses_a_pick_that_improves_nothing_beyond_noise():
    problems = gate(FLAT, answer(deciding=("timeNs",)))[1]
    assert problems == ["S1 R1 improves no metric beyond noise; generic picks only an option that improves one"]


def test_a_listed_perf_mode_refuses_a_trade_off_and_any_accepted_loss():
    problems = gate(FAST_HEAVY, answer(accepted=("allocationCount",)), LISTED)[1]
    assert problems == ["S1 R1 breaks perfMode latency+memAlloc's rule: a selected metric must improve and none worsen",
                        "accepted ['allocationCount']: perfMode latency+memAlloc accepts no loss"]


def test_a_listed_perf_mode_keeps_the_ratio_rule_of_the_verdict():
    clean = Option("R1", FAST_HEAVY.item, FAST_HEAVY.pins, "pass", (Estimate("timeNs", 0.6, 0.99, 40, AT),))
    assert gate(clean, answer(deciding=()), LISTED)[1] == []


def test_a_recommend_names_a_change_option_its_needs_and_no_edit():
    changed = Option("R1", "TypeA|ALG-B|P1", {}, "pass", (Estimate("timeNs", 0.5, 0.99, 40, AT),), change="local-edit",
                     diff=PairDiff("same", "same", "bytes", "persist"))
    good = {**answer(decision="recommend"), "members": [member(edits=[], needs=["stored tags are 16 bytes"])]}
    decision, problems = gate(changed, good)
    assert problems == [] and decision["replacements"][0]["decision"] == "recommend"
    assert decision["replacements"][0]["needs"] == ["stored tags are 16 bytes"] and decision["replacements"][0]["edits"] == []
    assert any("no change line" in p for p in gate(FAST_HEAVY, good)[1])
    assert any("lists its needs" in p for p in gate(changed, {**good, "members": [member(edits=[])]})[1])
    assert any("applies no edit" in p for p in gate(changed, {**good, "members": [member(needs=["x"])]})[1])


def test_concerns_are_stored_and_only_their_length_is_gated():
    decision, problems = gate(FAST_HEAVY, answer(accepted=("allocationCount",), concerns=("the input size looks synthetic",)))
    assert problems == [] and decision["replacements"][0]["concerns"] == ["the input size looks synthetic"]
    assert gate(FAST_HEAVY, {**KEEP, "concerns": ["x" * 301]})[1] == ["concerns[0] is longer than 300 characters"]
    assert gate(FAST_HEAVY, {**KEEP, "concerns": ["a"] * 6})[1] == ["concerns holds 6, at most 5"]


def test_the_render_shows_the_code_labels_and_the_rule():
    from perfrepair.ai.suggest.site_replace.render import render
    text = render(item(dossier(options=(FAST_HEAVY,))), GENERIC_MODE)
    assert "label: trade_off (improved timeNs; worse allocationCount)" in text and "rule overall" in text
    assert "rule strict" in render(item(dossier(options=(FAST_HEAVY,))), LISTED)


def _run(tmp_path, a):
    app = tmp_path / APP
    app.mkdir(parents=True)
    (app / "app.json").write_text(json.dumps({"root": str(tmp_path.resolve())}))
    (app / "dossiers.json").write_text(json.dumps(doc(a)))
    return tmp_path, app


def test_a_prompts_override_opens_its_own_outbox_and_removing_it_resumes_the_earlier_one(tmp_path):
    run, app = _run(tmp_path, dossier())
    replace(run, APP, ScriptedConversations(lambda *_: KEEP), LIBRARY, **QUIET)
    packaged = active_fingerprint(app / "replace")
    folder = tmp_path / "prompts" / "suggest"
    folder.mkdir(parents=True)
    (folder / "site-replace.system.md").write_text(LIBRARY.texts["suggest/site-replace"] + "\nAn owner's wording.\n")
    override = PromptLibrary.load(tmp_path / "prompts")
    asked = ScriptedConversations(lambda *_: answer())
    replace(run, APP, asked, override, **QUIET)
    assert active_fingerprint(app / "replace") != packaged and asked.started == 1
    assert read_json(app / "replacements.json")["replacements"][0]["decision"] == "replace"
    back = ScriptedConversations(lambda *_: answer())
    replace(run, APP, back, LIBRARY, **QUIET)
    assert active_fingerprint(app / "replace") == packaged and back.started == 0
    assert read_json(app / "replacements.json")["replacements"][0]["decision"] == "keep"


def test_edits_stay_exact_for_a_trade_off():
    bad = answer(edits=[edit("set_provider", "P9")], accepted=("allocationCount",))
    assert any("names 'P9'" in p for p in gate(FAST_HEAVY, bad)[1])
