import json
from dataclasses import replace
from pathlib import Path

import pytest
import yaml
from helpers import LIBRARY, QUIET

from perfrepair.ai.parse.algorithm_classify.command import DRY_RUN, Reviewer
from perfrepair.ai.parse.grouping_assign.kind import GroupingKind
from perfrepair.ai.runtime.agent import ScriptedConversations
from perfrepair.catalog.screening import SCREENING, PlatformRule
from perfrepair.check.run import validate_run
from perfrepair.data_handler.inbound.__main__ import main as inbound
from perfrepair.dto.classify import Batch, Evidence
from perfrepair.dto.screen import UNKNOWN, Verdict, lowers_status, read_screen, with_answer
from perfrepair.grouping.__main__ import main as grouping_main
from perfrepair.grouping.build import stage
from perfrepair.grouping.build.stage import build_stage
from perfrepair.run_dir import GroupingPaths
from perfrepair.screen.catalog import load_catalog
from perfrepair.screen.evidence import batches
from perfrepair.validation import ValidationFailed
from perfrepair.validation.grouping.output import read_groups
from perfrepair.validation.parse.algorithm_classify import check_reply

F = Path(__file__).parent / "fixtures" / "results" / "manifest.yaml"
PACKAGED = load_catalog(SCREENING)


def ev(n, name="X"):
    return Evidence(n, "MessageDigest", name, name, "P", "digest.none", True, None, "a.B", {})


BATCH = Batch((ev(3), ev(4)))


def answers(*rows):
    return json.dumps({"answers": [{"id": i, "answer": a, "reason": r} for i, a, r in rows]})


def test_the_gate_accepts_one_answer_per_listed_id_sorted_and_trimmed():
    decision, problems = check_reply(answers((4, "accepted", " listed "), (3, "unsure", "r")), BATCH)
    assert problems == [] and decision == {"answers": [{"id": 3, "answer": "unsure", "reason": "r"},
                                                       {"id": 4, "answer": "accepted", "reason": "listed"}]}


@pytest.mark.parametrize("reply, problem", [
    (answers((3, "unsure", "r"), (9, "unsure", "r")), "answers[1]: id 9 is not one of the listed ids [3, 4]"),
    (answers((3, "unsure", "r"), (3, "unsure", "r"), (4, "unsure", "r")), "answers[1]: id 3 is answered twice"),
    (answers((3, "unsure", "r")), "id 4 has no answer"),
    (answers((3, "weak", "r"), (4, "unsure", "r")), "answers[0]: answer 'weak' is not one of"),
    (answers((3, "unsure", " "), (4, "unsure", "r")), "answers[0]: reason is empty"),
    ('{"answers": {}}', "answers is not a list"),
    ("not json", "reply is not JSON"),
])
def test_the_gate_refuses_unlisted_repeated_missing_ids_other_values_and_empty_reasons(reply, problem):
    decision, problems = check_reply(reply, BATCH)
    assert decision is None and any(p.startswith(problem) for p in problems), problems


def test_trust_is_asymmetric_deprecated_is_broken_accepted_only_unverified_unsure_unchanged():
    unknown = Verdict(UNKNOWN, "no screening row", None, "X", None)
    assert with_answer(unknown, "deprecated", "withdrawn", "f" * 12) == Verdict(
        "broken", "withdrawn", "model:" + "f" * 12, "X", None)
    assert with_answer(unknown, "accepted", "listed", "f" * 12).status == "unverified"
    assert with_answer(unknown, "unsure", "?", "f" * 12) is unknown


def test_an_unverified_target_is_allowed_only_as_the_same_algorithm():
    current = Verdict("accepted", "r", "s", "Y")
    same, other = Verdict("unverified", "r", "model:x", "X"), Verdict("unverified", "r", "model:x", "Z")
    assert lowers_status(current, other)
    assert not lowers_status(same, replace(same, reason="from another provider"))
    assert lowers_status(current, Verdict("unverified", "r", "model:x", "Y"))


def test_unverified_and_unknown_rank_equal_under_accepted_for_the_same_algorithm():
    unknown, unverified = Verdict("unknown", "r", None, "X"), Verdict("unverified", "r", "model:x", "X")
    assert not lowers_status(unknown, unverified) and not lowers_status(unverified, unknown)
    assert lowers_status(Verdict("accepted", "r", "s", "X"), unknown)
    assert lowers_status(Verdict("accepted", "r", "s", "X"), unverified)
    assert lowers_status(unknown, Verdict("broken", "r", "s", "X"))


def test_the_app_gate_raises_an_unverified_verdict_to_platform_deprecated():
    rule = PlatformRule(28, None, "targetSdk", "gone", "S")
    handler = replace(PACKAGED, screening=replace(PACKAGED.screening, platform={("P", "MessageDigest", "X"): rule})).handler()
    unverified = Verdict("unverified", "r", "model:x", "X")
    assert handler.for_app(unverified, "MessageDigest", "P", 28).status == "platform_deprecated"
    assert handler.for_app(unverified, "MessageDigest", "P", 27) == unverified


def test_batches_have_a_fixed_size_and_ids_as_their_key():
    out = batches([ev(n) for n in range(1, 24)], size=10)
    assert [len(b.members) for b in out] == [10, 10, 3] and out[2].key == "21,22,23"


def _undecided(catalog):
    """The fixture catalog without its digest and MAC rows: items 3 (SHA-256) and 4 (HmacSHA256) are unknown."""
    crypto = {k: v for k, v in catalog.screening.crypto.items() if k[0] not in ("MessageDigest", "Mac")}
    return replace(catalog, screening=replace(catalog.screening, crypto=crypto))


def classifier(task, *_):
    blocks = {int(b.split("\n")[0]): b for b in task.text.split("\nid ")[1:]}
    return {"answers": [{"id": i, "answer": "deprecated" if "name: SHA-256\n" in b else "accepted",
                         "reason": f"model on {i}"} for i, b in blocks.items()]}


@pytest.fixture
def reviewed(tmp_path):
    assert inbound(["--manifest", str(F), "-o", str(tmp_path)]) == 0
    scripted = ScriptedConversations(classifier)
    paths = build_stage(F, tmp_path, _undecided(PACKAGED), Reviewer(scripted, LIBRARY), **QUIET)
    return paths, scripted


def test_build_with_a_reviewer_applies_the_answers_and_writes_the_candidates(reviewed):
    paths, scripted = reviewed
    doc = json.loads(paths.screen.read_text())
    fingerprint = doc["review"]["fingerprint"]
    verdicts = read_screen(doc)
    assert (verdicts[3].status, verdicts[3].source) == ("broken", f"model:{fingerprint}")
    assert (verdicts[4].status, verdicts[4].reason) == ("unverified", "model on 4")
    assert verdicts[1].status == "accepted" and scripted.started == 1
    [row] = yaml.safe_load(paths.registry_candidates.read_text())["candidates"]
    assert row == {"id": 4, "type": "Mac", "name": "HmacSHA256", "canonical": "HmacSHA256", "provider": "Slow",
                   "reason": "model on 4", "fingerprint": fingerprint}
    message = scripted.turns[0][2].text
    assert "className: a.B" in message and "trial: instantiates" in message and "id 1\n" not in message


def test_a_model_deprecated_item_is_grouped_by_code_and_never_asked_by_assign(reviewed):
    paths, _ = reviewed
    kind = GroupingKind(paths)
    assert 3 not in [i.id for i in kind.pending()] and 4 in [i.id for i in kind.pending()]
    assert any(g.members == [3] for g in kind.empty().groups.values())


def test_the_reviewed_run_validates_and_tampering_is_found(reviewed):
    paths, _ = reviewed
    run = paths.root.parent
    out = validate_run(run, PACKAGED)
    assert out["grouping/screen.json"] == [] and out["grouping/classify"] == []
    doc = json.loads(paths.screen.read_text())
    doc["verdicts"]["4"]["status"] = "accepted"
    paths.screen.write_text(json.dumps(doc))
    assert validate_run(run, PACKAGED)["grouping/classify"] == [
        f"4: classify answered accepted, screen.json says accepted from model:{doc['review']['fingerprint']}"]


def test_a_rebuild_resumes_the_outbox_and_another_unknown_set_rotates_it(reviewed, tmp_path):
    paths, _ = reviewed
    again = ScriptedConversations(classifier)
    build_stage(F, tmp_path, _undecided(PACKAGED), Reviewer(again, LIBRARY), **QUIET)
    assert again.started == 0
    first = json.loads(paths.screen.read_text())["review"]["fingerprint"]
    only_mac = replace(PACKAGED, screening=replace(PACKAGED.screening, crypto={
        k: v for k, v in PACKAGED.screening.crypto.items() if k[0] != "Mac"}))
    build_stage(F, tmp_path, only_mac, Reviewer(again, LIBRARY), **QUIET)
    second = json.loads(paths.screen.read_text())["review"]["fingerprint"]
    assert second != first and again.started == 1
    assert validate_run(tmp_path, PACKAGED)["grouping/classify"] == []


def test_the_dry_run_answers_unsure_so_no_verdict_changes(tmp_path):
    assert inbound(["--manifest", str(F), "-o", str(tmp_path)]) == 0
    plain = read_screen(json.loads(build_stage(F, tmp_path, _undecided(PACKAGED), **QUIET).screen.read_text()))
    paths = build_stage(F, tmp_path, _undecided(PACKAGED), Reviewer(DRY_RUN, LIBRARY), **QUIET)
    assert read_screen(json.loads(paths.screen.read_text())) == plain
    assert yaml.safe_load(paths.registry_candidates.read_text())["candidates"] == []


def test_a_batch_whose_every_answer_is_refused_stays_unknown(tmp_path):
    assert inbound(["--manifest", str(F), "-o", str(tmp_path)]) == 0
    wrong = ScriptedConversations(lambda *_: {"answers": [{"id": 99, "answer": "accepted", "reason": "r"}]})
    paths = build_stage(F, tmp_path, _undecided(PACKAGED), Reviewer(wrong, LIBRARY), **QUIET)
    verdicts = read_screen(json.loads(paths.screen.read_text()))
    assert {verdicts[3].status, verdicts[4].status} == {"unknown"} and wrong.started == 2
    saved = json.loads(paths.classified.read_text())["answers"]
    assert {a["answer"] for a in saved.values()} == {"unsure"} and saved["3"]["reason"].startswith("dropped: ")
    assert validate_run(tmp_path, PACKAGED)["grouping/classify"] == []


def test_the_command_reviews_only_with_ai_review_on(tmp_path, capsys):
    config = tmp_path / "perfrepair.yaml"
    config.write_text("screening: {aiReview: true}\n")
    run = tmp_path / "run"
    assert grouping_main(["build", "--manifest", str(F), "--run", str(run), "--perfrepair-config", str(config),
                          "--agent", "dry-run"]) == 0
    assert "aiReview on" in capsys.readouterr().err
    doc = json.loads(GroupingPaths(run).screen.read_text())
    assert "review" in doc and GroupingPaths(run).classified.is_file()
    assert grouping_main(["build", "--manifest", str(F), "--run", str(tmp_path / "off")]) == 0
    assert "review" not in json.loads(GroupingPaths(tmp_path / "off").screen.read_text())


def _fewer_items(monkeypatch):
    """Another manifest's build: the same items without the last one."""
    real = stage.build

    def build(*args):
        items, profiles = real(*args)
        return items[:-1], {k: v for k, v in profiles.items() if k != items[-1].id}
    monkeypatch.setattr(stage, "build", build)


def test_a_build_that_fails_in_classify_leaves_the_previous_build_whole(tmp_path, monkeypatch):
    assert inbound(["--manifest", str(F), "-o", str(tmp_path)]) == 0
    paths = build_stage(F, tmp_path, PACKAGED, **QUIET)
    before = {p.name: p.read_bytes() for p in (paths.items, paths.profiles, paths.screen)}
    _fewer_items(monkeypatch)

    def lost(*_):
        raise RuntimeError("connection lost")
    with pytest.raises(RuntimeError):
        build_stage(F, tmp_path, _undecided(PACKAGED), Reviewer(ScriptedConversations(lost), LIBRARY), **QUIET)
    assert {p.name: p.read_bytes() for p in (paths.items, paths.profiles, paths.screen)} == before
    assert len(GroupingKind(paths).items()) == 4


def test_screen_json_beside_another_builds_items_is_refused_by_assign_and_read_groups(tmp_path, monkeypatch):
    assert inbound(["--manifest", str(F), "-o", str(tmp_path)]) == 0
    old = build_stage(F, tmp_path, PACKAGED, **QUIET).screen.read_bytes()
    _fewer_items(monkeypatch)
    paths = build_stage(F, tmp_path, PACKAGED, **QUIET)
    paths.screen.write_bytes(old)
    with pytest.raises(ValidationFailed, match="built from another items.json"):
        GroupingKind(paths)
    paths.groups.write_text("{}")
    with pytest.raises(ValidationFailed, match="built from another items.json"):
        read_groups(paths)
    assert "built from another items.json" in validate_run(tmp_path, PACKAGED)["grouping/screen.json"][0]
