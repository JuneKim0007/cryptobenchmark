"""A broken use: never a broken option, the list or the model's secure choice, an edit or a person's, one report line."""
import json
from dataclasses import replace

import pytest
from helpers import LIBRARY, QUIET, row, summary

from perfrepair import run_dir as rd
from perfrepair.ai.repair.upgrade.command import upgrade
from perfrepair.ai.repair.upgrade.render import render
from perfrepair.ai.runtime.agent import ScriptedConversations
from perfrepair.catalog.types import types
from perfrepair.catalog.upgrades import Upgrades, UpgradesError, upgrades
from perfrepair.dto.perf_mode import PerfMode
from perfrepair.dto.screen import Verdict, refused_target
from perfrepair.dto.site import REPLACEMENTS_SCHEMA_VERSION, SCOPES_SCHEMA_VERSION, Scope, scope_id
from perfrepair.dto.unit import Unit, unit_id
from perfrepair.dto.upgrade import Upgrade, UpgradeItem
from perfrepair.repair.__main__ import _load
from perfrepair.report.markdown import _broken_uses
from perfrepair.result.candidates import Family
from perfrepair.result.dossier import build_dossiers
from perfrepair.result.unit_dossiers import by_unit
from perfrepair.result.upgrades import needs_person
from perfrepair.validation.dossiers.against_run import validate_dossiers
from perfrepair.validation.upgrade import check_reply

LATENCY = PerfMode(("latency",))
APP = "app"
MD5, MD5_OTHER = "MessageDigest|MD5|P1", "MessageDigest|MD5|P2"
SHA1 = "MessageDigest|SHA-1|P1"
SHA256, SHA512, SHA224 = "MessageDigest|SHA-256|P1", "MessageDigest|SHA-512|P1", "MessageDigest|SHA-224|P1"
ITEMS = (MD5, MD5_OTHER, SHA1, SHA256, SHA512, SHA224)
NAME = {q: q.split("|")[1] for q in ITEMS}
STATUS = {MD5: "broken", MD5_OTHER: "broken", SHA1: "broken", SHA256: "accepted", SHA512: "accepted", SHA224: "accepted"}
GROUPS = {"groups": [{"id": "g", "members": [1, 2]}],
          "items": {str(n): {"qualified": q, "group": "g" if n < 3 else None, "runs": True} for n, q in enumerate(ITEMS, 1)},
          "interop": {"status": "not_run", "pairs": []}}
VERDICTS = {q: Verdict(STATUS[q], "r", "S", NAME[q]) for q in ITEMS}
# the slowest current, and SHA-512 proven slower than the broken one: no_gain would remove it
MEDIANS = {MD5: 100, MD5_OTHER: 90, SHA1: 80, SHA256: 300, SHA512: 200, SHA224: 50}


def _rows(names=ITEMS):
    rows = [replace(row(q, q.split("|")[2], algorithm=NAME[q], type_="MessageDigest", key_size=None, key_kind="none"),
                    parameters={}) for q in names]
    return rows, {r.rowId: {"timeNs": summary(MEDIANS[r.rowId])} for r in rows}


def _scope(algorithm="MD5", sinks=("return",)):
    return replace(Scope(scope_id(APP, "A.java", "f", 2, "MessageDigest.getInstance"), APP, "A.java", 2, "MessageDigest.getInstance",
                         "f", 1, 3, "MessageDigest", algorithm, "P1", "explicit", None, 64), sinks=sinks)


def _family(max_change="drop-in", listed=None):
    return Family({q: "digest.none" for q in ITEMS}, NAME, types(), 30, frozenset(), max_change,
                  upgrades() if listed is None else listed)


def _doc(tmp_path, s=None, names=ITEMS, family=None, verdicts=VERDICTS, units=None):
    s = s or _scope()
    (tmp_path / "A.java").write_text("void f() {\n  MessageDigest.getInstance(\"MD5\", \"P1\");\n}\n")
    rows, measurements = _rows(names)
    doc = build_dossiers(APP, [s], {"bundled": []}, GROUPS, rows, measurements, tmp_path, verdicts, LATENCY,
                         family or _family(), {"P1", "P2"})
    return by_unit(doc, units or [Unit(unit_id(APP, [s.id]), (s.id,), (), ())], [s], GROUPS)


def _write(tmp_path, doc):
    paths = rd.AppPaths(tmp_path, APP)
    paths.root.mkdir(parents=True, exist_ok=True)
    paths.dossiers.write_text(json.dumps(doc))
    return paths


def _never_asked(*_):
    raise AssertionError("no model call")


def _state(tmp_path, doc, conversations=None):
    _write(tmp_path, doc)
    return upgrade(tmp_path, APP, conversations or ScriptedConversations(_never_asked), LIBRARY, **QUIET)


@pytest.mark.parametrize("current, target, refused", [
    (VERDICTS[MD5], VERDICTS[SHA1], True), (VERDICTS[MD5], VERDICTS[MD5_OTHER], True), (VERDICTS[MD5], VERDICTS[SHA256], False)])
def test_a_broken_target_is_refused_always_even_the_same_algorithm_from_another_provider(current, target, refused):
    assert refused_target(current, target) is refused


def test_neither_broken_nor_another_provider_of_it_is_offered(tmp_path):
    doc = _doc(tmp_path)
    assert doc["dossiers"] == [] and [n["reason"] for n in doc["noOptions"]] == ["broken_use"]
    offered = [o["item"] for r in doc["upgrades"] for o in r["options"]]
    assert MD5_OTHER not in offered and SHA1 not in offered and MD5 not in offered
    assert validate_dossiers(doc, [_scope()], GROUPS, VERDICTS) == []


def test_the_validator_refuses_a_broken_option_in_an_upgrades_row(tmp_path):
    doc = _doc(tmp_path)
    doc["upgrades"][0]["options"][0] |= {"item": SHA1, "screen": "broken"}
    assert any("is not accepted" in p for p in validate_dossiers(doc, [_scope()], GROUPS, VERDICTS))


def test_a_listed_upgrade_is_the_lists_targets_best_first_whatever_no_gain_says_and_asks_no_model(tmp_path):
    doc = _doc(tmp_path, _scope(sinks=("local",)))
    [row_] = doc["upgrades"]
    # SHA-224 is the fastest accepted one, but the list leaves it out; both listed are slower than MD5
    assert [o["item"] for o in row_["options"]] == [SHA512, SHA256] and row_["identified"]
    assert {"item": SHA224, "reason": "not_listed"} in [{"item": n["item"], "reason": n["reasons"][0]} for n in doc["notOffered"]]
    state = _state(tmp_path, doc)
    [u] = state.rows.values()
    assert (u.status, u.option, u.source) == ("upgraded", SHA512, "list")
    assert [e.kind for e in u.edits] == ["set_algorithm"] and u.edits[0].algorithm == "SHA-512"


def test_an_unlisted_broken_use_is_asked_once_and_chooses_among_the_accepted_measured(tmp_path):
    doc = _doc(tmp_path, family=_family(listed=Upgrades({})))
    [row_] = doc["upgrades"]
    assert not row_["identified"] and [o["item"] for o in row_["options"]] == [SHA224, SHA512, SHA256]
    asked = []
    agent = ScriptedConversations(lambda m, *_: asked.append(m.text) or {"option": "R2", "reason": "fits"})
    state = _state(tmp_path, doc, agent)
    assert len(asked) == 1 and state.rows[row_["scope"]["id"]].option == SHA512
    assert state.rows[row_["scope"]["id"]].source == "llm"
    # a rerun resumes the outbox: the same item is not asked again
    _state(tmp_path, doc, agent)
    assert len(asked) == 1


def test_a_list_with_no_measured_target_falls_to_the_model_among_what_is_measured(tmp_path):
    names = (MD5, MD5_OTHER, SHA1, SHA224)
    doc = _doc(tmp_path, names=names)
    assert not doc["upgrades"][0]["identified"] and [o["item"] for o in doc["upgrades"][0]["options"]] == [SHA224]


def test_the_gate_takes_only_an_offered_alias_and_a_reason(tmp_path):
    item = UpgradeItem.from_json(_doc(tmp_path, family=_family(listed=Upgrades({})))["upgrades"][0])
    assert check_reply('{"option": "R9", "reason": "x"}', item)[0] is None
    assert check_reply('{"option": "R1", "reason": " "}', item)[0] is None
    assert check_reply('{"option": "R1", "reason": "x"}', item)[0] == {"option": SHA224, "reason": "x"}


@pytest.mark.parametrize("sinks, need", [(("persist",), "persisted_data"), (("network",), "wire_format"), (("unknown",), "unknown_sink")])
def test_stored_or_sent_output_is_a_persons_never_an_edit(tmp_path, sinks, need):
    [u] = _state(tmp_path, _doc(tmp_path, _scope(sinks=sinks))).rows.values()
    assert (u.status, u.edits) == ("needs_migration", ()) and need in u.needs and u.option == SHA512


def test_local_output_goes_through_the_edit_step(tmp_path):
    state = _state(tmp_path, _doc(tmp_path, _scope(sinks=("local",))))
    [u] = state.rows.values()
    assert u.status == "upgraded"
    assert u.replacement().decision == "replace" and u.replacement().edits == u.edits


def test_a_linked_member_is_a_persons(tmp_path):
    s = _scope()
    units = [Unit(unit_id(APP, [s.id, "other"]), (s.id, "other"), (), ())]
    doc = _doc(tmp_path, s, units=units)
    assert doc["upgrades"][0]["linked"] == ["other"]
    [u] = _state(tmp_path, doc).rows.values()
    assert u.status == "needs_migration" and "linked_members" in u.needs


def test_no_accepted_option_is_a_report_line_and_the_run_goes_on(tmp_path):
    doc = _doc(tmp_path, names=(MD5, MD5_OTHER, SHA1))
    assert doc["upgrades"] == [] and [n["reason"] for n in doc["noOptions"]] == ["no_secure_option"]
    assert validate_dossiers(doc, [_scope()], GROUPS, VERDICTS) == []
    [u] = _state(tmp_path, doc).rows.values()
    assert (u.status, u.option, u.source) == ("no_secure_option", None, "static")


def test_a_dropped_answer_is_a_persons_not_an_edit(tmp_path):
    doc = _doc(tmp_path, family=_family(listed=Upgrades({})))
    agent = ScriptedConversations(lambda *_: {"option": "R9", "reason": "x"})
    [u] = _state(tmp_path, doc, agent).rows.values()
    assert (u.status, u.source, u.needs) == ("needs_migration", "fallback", ("model_dropped",))


def test_the_slice_shows_the_site_sinks_reach_and_candidates_only(tmp_path):
    item = UpgradeItem.from_json(_doc(tmp_path, family=_family(listed=Upgrades({})))["upgrades"][0])
    text = render(item)
    assert "sinks: return" in text and "reach: return" in text and f"R1 = {SHA224}" in text and "timeNs 50" in text
    assert "FUNCTION SOURCE" not in text and "EDIT KINDS" not in text


def test_an_upgraded_row_reaches_the_edit_step_over_replace_s_static_keep(tmp_path):
    paths = _write(tmp_path, {})
    keep = {"scope": "s", "decision": "keep", "option": None, "edits": [], "risks": [], "reason": "broken_use"}
    paths.replacements.write_text(json.dumps({"schemaVersion": REPLACEMENTS_SCHEMA_VERSION, "replacements": [keep]}))
    paths.scopes.write_text(json.dumps({"schemaVersion": SCOPES_SCHEMA_VERSION, "scopes": []}))
    row_ = Upgrade("s", MD5, "upgraded", SHA512, "list", "r").to_json()
    paths.upgrades.write_text(json.dumps({"schemaVersion": 1, "app": APP, "upgrades": [row_]}))
    _, replacements = _load(paths)
    assert replacements["s"].decision == "replace" and replacements["s"].option == SHA512


def test_the_report_section_says_what_each_became():
    uses = {"counts": {"upgraded": 1, "needs_migration": 1}, "rows": [
        {"file": "A.java", "line": 2, "function": "f", "current": MD5, "status": "upgraded", "option": SHA512, "source": "list",
         "needs": [], "reason": "r", "review": ["reach_return_unverified"]},
        {"file": "B.java", "line": 4, "function": "g", "current": SHA1, "status": "needs_migration", "option": SHA256, "source": "list",
         "needs": ["persisted_data"], "reason": "r", "review": []}]}
    lines = _broken_uses({"brokenUses": uses})
    assert "## Broken uses" in lines and "upgraded 1, needs_migration 1." in lines
    assert any("persisted_data" in line and "B.java:4" in line for line in lines)
    assert _broken_uses({"brokenUses": {"counts": {}, "rows": []}}) == []


def test_the_list_refuses_a_target_that_is_not_accepted_or_a_name_that_is_not_broken(tmp_path):
    bad = tmp_path / "u.yaml"
    bad.write_text("schemaVersion: 1\nfamilies:\n  digest.none:\n    SHA-256:\n      - {name: MD5, source: R2}\n      - {name: SHA-512, source: NOPE}\n")
    with pytest.raises(UpgradesError) as e:
        Upgrades.load(bad)
    assert "upgrades_not_broken" in str(e.value) and "upgrades_target" in str(e.value) and "upgrades_source" in str(e.value)


def test_every_listed_row_has_a_source_and_targets():
    assert upgrades().rows and all(targets and all(t.source for t in targets) for targets in upgrades().rows.values())
    assert upgrades().targets("digest.none", "md5") == upgrades().targets("digest.none", "MD5")


def _scoped(tmp_path, source, line):
    """The scope code reads from the source itself: its sinks and its lifecycle's facts, never written by hand."""
    pytest.importorskip("tree_sitter")
    from perfrepair.scope.build import build_scopes
    (tmp_path / "A.java").write_text(source)
    site = {"file": "A.java", "line": line, "call": 'MessageDigest.getInstance("MD5", "P1")', "engineType": "MessageDigest",
            "resolvedAlgorithm": "MD5", "resolvedProvider": "P1", "resolution": "explicit"}
    return build_scopes(APP, tmp_path, [site]).scopes[0]


# threema MasterKey.calcVerification: the digest is returned, stored by one caller and compared by others
CALC_VERIFICATION = """class A {
  private static byte[] calcVerification(byte[] key) {
    MessageDigest md = MessageDigest.getInstance("MD5", "P1");
    md.update(key);
    byte[] digest = md.digest();
    byte[] verification = new byte[4];
    System.arraycopy(digest, 0, verification, 0, 4);
    return verification;
  }
}
"""
COMPARED_HERE = """class A {
  static boolean same(byte[] a, byte[] b) {
    MessageDigest md = MessageDigest.getInstance("MD5", "P1");
    byte[] x = md.digest(a);
    byte[] y = md.digest(b);
    return Arrays.equals(x, y);
  }
}
"""
AGAINST_A_STORED_ONE = """class A {
  boolean check(byte[] key) {
    MessageDigest md = MessageDigest.getInstance("MD5", "P1");
    byte[] mine = md.digest(key);
    return Arrays.equals(mine, verification);
  }
}
"""


def test_a_returned_output_on_the_calc_verification_shape_is_a_persons(tmp_path):
    s = _scoped(tmp_path, CALC_VERIFICATION, 3)
    assert s.sinks == ("return",) and not s.lifecycle.outputCompared
    [u] = _state(tmp_path, _doc(tmp_path, s)).rows.values()
    assert (u.status, u.edits, u.option) == ("needs_migration", (), SHA512) and u.needs == ("reach_return_unverified",)


def test_a_returned_output_is_a_persons_even_when_the_option_lists_no_review(tmp_path):
    item = UpgradeItem.from_json(_doc(tmp_path)["upgrades"][0])
    assert needs_person(item, replace(item.dossier.options[0], needsReview=())) == ("reach_return_unverified",)


def test_a_comparison_with_a_reference_from_elsewhere_is_a_persons(tmp_path):
    s = _scoped(tmp_path, AGAINST_A_STORED_ONE, 3)
    assert s.sinks == ("return",) and not s.lifecycle.outputCompared
    [u] = _state(tmp_path, _doc(tmp_path, s)).rows.values()
    assert u.status == "needs_migration" and "reach_return_unverified" in u.needs


def test_an_output_compared_and_discarded_in_its_function_is_an_edit(tmp_path):
    s = _scoped(tmp_path, COMPARED_HERE, 3)
    assert s.sinks == ("return",) and s.lifecycle.outputCompared
    [u] = _state(tmp_path, _doc(tmp_path, s)).rows.values()
    assert (u.status, u.needs) == ("upgraded", ()) and "reach_return_unverified" in u.review


@pytest.mark.parametrize("reason", ["deterministic_lost", "strength_unknown"])
def test_a_refused_accepted_measured_member_is_a_persons_with_that_reason(tmp_path, reason, monkeypatch):
    import perfrepair.result.candidates as candidates
    real = candidates.classify

    def refuse(types_, s, mine, c, min_sdk):
        found = real(types_, s, mine, c, min_sdk)
        return replace(found, change="rejected", reasons=(reason,))
    monkeypatch.setattr(candidates, "classify", refuse)
    doc = _doc(tmp_path)
    assert doc["upgrades"] == [] and doc["noOptions"] == [{"scope": _scope().id, "reason": f"person_judges: {reason}"}]
    assert validate_dossiers(doc, [_scope()], GROUPS, VERDICTS) == []
    [u] = _state(tmp_path, doc).rows.values()
    assert (u.status, u.needs, u.option, u.source) == ("needs_migration", (reason,), None, "static")


def test_no_secure_option_only_when_the_family_has_no_accepted_measured_member(tmp_path, monkeypatch):
    import perfrepair.result.candidates as candidates
    real = candidates.classify

    def refuse(types_, s, mine, c, min_sdk):
        return replace(real(types_, s, mine, c, min_sdk), change="rejected", reasons=("deterministic_lost",))
    monkeypatch.setattr(candidates, "classify", refuse)
    doc = _doc(tmp_path, names=(MD5, MD5_OTHER, SHA1))
    assert [n["reason"] for n in doc["noOptions"]] == ["no_secure_option"]
