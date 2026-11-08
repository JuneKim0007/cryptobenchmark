"""The job template on a scripted transport: the log, the submit's checks, repass and escalation, tool scope, the spend cap."""
import json
from dataclasses import dataclass, replace

import pytest
import yaml
from helpers import LIBRARY, logged

from perfrepair.ai.attempt.escalate import next_tier
from perfrepair.ai.job import Job
from perfrepair.ai.log.attempt_log import AttemptLog
from perfrepair.ai.log.where import Where
from perfrepair.ai.model.tier import Ladder, Tier
from perfrepair.ai.review.job import ReviewJob
from perfrepair.ai.runtime.agent import AgentFailed, ScriptedConversations
from perfrepair.ai.runtime.engine.ask import Limits
from perfrepair.ai.runtime.engine.budget import Budget, OverBudget
from perfrepair.ai.runtime.engine.outbox import active_outbox
from perfrepair.ai.runtime.gateway.claude import GATEWAY as CLAUDE, MODELS as CLAUDE_MODELS
from perfrepair.ai.runtime.gateway.spawn import Spawned
from perfrepair.ai.tools.catalogue_read import LIST_GROUPS, VIEW_FOR
from perfrepair.ai.tools.registry import Registry
from perfrepair.ai.tools.tool import Context, args_schema
from perfrepair.dto.charter import charter_document

LADDER = Ladder(("small", "big"))
ONE = Limits(turns=1, sessions=1)


@dataclass(frozen=True)
class Thing:
    key: str


class Pick(Job):
    name = "pick"
    prompt = "parse/algorithm-classify"
    submit_description = "the chosen colour"
    submit_schema = args_schema({"colour": {"type": "string"}, "reason": {"type": "string", "pattern": r"\S"}}, ("colour", "reason"))

    def __init__(self, *args, things=("a",), **kwargs):
        self.things, self.kept = [Thing(k) for k in things], {}
        super().__init__(*args, **kwargs)

    def candidates(self):
        return self.things

    def render(self, item):
        return f"ITEM {item.key}: answer red or blue"

    def checks(self, item, args):
        return [] if args["colour"] in ("red", "blue") else [f"colour {args['colour']!r} is not red or blue"]

    def apply(self, item, record):
        self.kept[item.key] = record.decision


def submit(colour, reason="r"):
    return {"tool": "submit", "args": {"colour": colour, "reason": reason}}


def spawned(answer, budget=None, usage=None):
    """Every tier answers by the same function, told which model it is; usage: what each reply reports."""
    def at(tier):
        convos = ScriptedConversations(lambda task, s, t: answer(tier.model, task, s, t))
        return convos if usage is None else paid(convos, usage)
    tier = Tier("scripted", "small", "low")
    return Spawned(at(tier), tier, budget, at, LADDER)


def paid(convos, usage=None, **reported):
    """Each reply of these conversations reports usage (and any other reply field), as a transport would."""
    start = convos.start
    fields = {**({"usage": usage} if usage is not None else {}), **reported}

    def started(system, schema):
        c = start(system, schema)
        send = c._send
        c._send = lambda m: replace(send(m), **fields)
        return c
    convos.start = started
    return convos


def job(tmp_path, answer, limits=Limits(), budget=None, **kw):
    return job_of(Pick, tmp_path, answer, limits, budget, **kw)


def job_of(cls, tmp_path, answer=lambda *_: submit("red"), limits=Limits(), budget=None, usage=None, **kw):
    log = AttemptLog(tmp_path, cls.name, Where("test", cls.name), echo=lambda _: None)
    return cls(spawned(answer, budget, usage), LIBRARY, log, Registry(), limits, store=tmp_path / cls.name, **kw)


def test_the_log_is_opened_at_the_start_even_when_the_job_asks_nothing(tmp_path):
    assert job(tmp_path, lambda *_: submit("red"), things=()).run() == 0
    assert (tmp_path / "log/ai/pick.yaml").is_file() and logged(tmp_path, "pick") == []


def test_the_log_is_appended_never_rewritten_and_numbers_on_across_runs(tmp_path):
    j = job(tmp_path, lambda *_: submit("red", reason="first line\n- not an entry\n  third"), things=("a",))
    j.run()
    path = tmp_path / "log/ai/pick.yaml"
    before = path.read_text()
    job(tmp_path, lambda *_: submit("blue"), things=("a", "b")).run()
    assert path.read_text().startswith(before)
    entries = logged(tmp_path, "pick")
    assert [(e["n"], e["item"]) for e in entries] == [(1, "a"), (2, "b")] and entries[0]["submitted"]["reason"].startswith("first")


def test_an_empty_whole_document_log_is_taken_over_by_the_appending_one(tmp_path):
    path = tmp_path / "log/ai/pick.yaml"
    path.parent.mkdir(parents=True)
    path.write_text(yaml.safe_dump({"schemaVersion": 1, "job": "pick", "attempts": []}))
    job(tmp_path, lambda *_: submit("red")).run()
    assert [e["n"] for e in logged(tmp_path, "pick")] == [1]


def test_the_log_is_written_when_the_provider_fails(tmp_path):
    def broken(*_):
        raise AgentFailed("claude_cli_failed", "usage limit")
    with pytest.raises(AgentFailed):
        job(tmp_path, broken).run()
    [entry] = logged(tmp_path, "pick")
    assert entry["outcome"] == "failed" and "usage limit" in entry["error"] and active_outbox(tmp_path / "pick").records() == []


def test_an_interrupt_is_logged_as_interrupted_with_its_error_and_raised(tmp_path):
    def ctrl_c(*_):
        raise KeyboardInterrupt
    with pytest.raises(KeyboardInterrupt):
        job(tmp_path, ctrl_c).run()
    [entry] = logged(tmp_path, "pick")
    assert entry["outcome"] == "interrupted" and entry["error"] == "KeyboardInterrupt" and "reason" not in entry


def test_a_provider_failure_on_a_later_turn_keeps_the_earlier_turns_and_their_tokens(tmp_path):
    def answer(model, task, session, turn):
        if turn == 1:
            return {"tool": "list_groups", "args": {}}
        raise AgentFailed("claude_cli_failed", "usage limit")
    j = job_of(Pick, tmp_path, answer, budget=Budget("apps.replace.budget", 100000, spend=10**6),
               usage={"input": 3, "output": 4, "costUsd": 0.5})
    with pytest.raises(AgentFailed):
        j.run()
    [entry] = logged(tmp_path, "pick")
    assert entry["outcome"] == "failed" and [t["status"] for t in entry["turns"]] == ["tool"]
    assert entry["tokens"]["input"] == 3 and entry["costUsd"] == 0.5 and j.spawned.budget.used == 7


def test_submit_runs_the_checks_and_its_problem_is_the_next_turn(tmp_path):
    seen = []

    def answer(model, task, session, turn):
        seen.append(turn)
        return submit("green") if turn == 1 else submit("blue")
    j = job(tmp_path, answer)
    assert j.run() == 1 and j.kept["a"]["colour"] == "blue"
    [entry] = logged(tmp_path, "pick")
    assert [c["ok"] for c in entry["calls"]] == [False, True] and "not red or blue" in entry["calls"][0]["problem"]
    assert entry["outcome"] == "decided" and entry["submitted"]["colour"] == "blue"


def test_repass_stops_at_two_then_escalates_then_drops(tmp_path):
    asked = []

    def answer(model, task, session, turn):
        asked.append((model, task.text))
        return submit("green")
    j = job(tmp_path, answer, ONE)
    assert j.run() == 1
    entries = logged(tmp_path, "pick")
    assert [e["tier"]["model"] for e in entries] == ["small"] * 3 + ["big"] * 3
    assert [e["reason"]["source"] for e in entries] == ["checks"] * 6
    assert "attempt 2 was refused: checks" in asked[2][1] and "EARLIER ATTEMPTS" not in asked[3][1]
    [record] = active_outbox(tmp_path / "pick").records()
    assert record.outcome == "dropped" and record.tier["model"] == "big"


def test_an_escalated_answer_records_the_tier_and_the_model_that_gave_it(tmp_path):
    j = job(tmp_path, lambda model, *_: submit("red") if model == "big" else submit("green"), ONE)
    assert j.run() == 1
    [record] = active_outbox(tmp_path / "pick").records()
    assert record.outcome == "decided" and record.tier["model"] == "big" and record.answered == "scripted"


def test_a_job_cannot_call_another_jobs_tool(tmp_path):
    registry = Registry()
    log = AttemptLog(tmp_path, "pick", Where("test", "pick"))
    Pick(spawned(lambda *_: submit("red")), LIBRARY, log, registry)

    class Other(Pick):
        name = "other"
        submit_name = "choose"
    Other(spawned(lambda *_: submit("red")), LIBRARY, log, registry)
    tool, out = registry.call(Context("pick", "a"), "choose", {"colour": "red", "reason": "r"})
    assert tool is None and not out.ok and out.text.startswith("unknown tool 'choose'")
    assert [d["name"] for d in registry.surface("pick")] == ["view_for", "what_is", "list_groups", "get_group", "submit"]


def test_a_call_outside_the_schema_is_a_problem_not_a_run(tmp_path):
    replies = iter([{"tool": "submit", "args": {"colour": 3}}, {"tool": "submit", "args": {"colour": "red"}}, submit("red")])
    j = job(tmp_path, lambda *_: next(replies))
    assert j.run() == 1
    [entry] = logged(tmp_path, "pick")
    assert entry["turns"][0]["problems"] == ["args.colour is not a string"]
    assert len(entry["calls"]) == 2 and entry["calls"][0]["problem"] == "reason is missing"


def test_a_read_tool_answers_and_the_model_then_submits(tmp_path):
    replies = iter([{"tool": "list_groups", "args": {}}, submit("red")])
    j = job(tmp_path, lambda *_: next(replies))
    assert j.run() == 1
    [entry] = logged(tmp_path, "pick")
    assert [t["status"] for t in entry["turns"]] == ["tool", "accepted"] and entry["calls"][0]["tool"] == "list_groups"


def test_a_subclass_cannot_replace_the_template():
    with pytest.raises(TypeError, match="overrides run"):
        class Sneaky(Pick):
            def run(self, limit=None):
                return 0


def test_a_subclass_cannot_skip_the_reviewer():
    with pytest.raises(TypeError, match="overrides _review"):
        class NoReview(Pick):
            def _review(self, item, submitted):
                return None, None


def test_a_template_assigned_after_the_class_is_refused_at_instantiation(tmp_path):
    class Later(Pick):
        name = "later"
    Later.run = lambda self, limit=None: 0
    with pytest.raises(TypeError, match="replaces run"):
        job_of(Later, tmp_path)
    assert not (tmp_path / "log/ai/later.yaml").exists()


def test_a_parent_init_subclass_without_super_does_not_unseal_its_children(tmp_path):
    class Middle(Pick):
        def __init_subclass__(cls, **kw):
            pass

    class Leaf(Middle):
        name = "leaf"

        def _item(self, item):
            return None
    with pytest.raises(TypeError, match="replaces _item"):
        job_of(Leaf, tmp_path)


def test_an_instance_cannot_replace_the_template(tmp_path):
    j = job(tmp_path, lambda *_: submit("red"))
    with pytest.raises(TypeError, match="sets _review"):
        j._review = lambda *_: (None, None)


def test_the_charter_hashes_the_tools_and_never_the_model_or_tier(tmp_path):
    j = job(tmp_path, lambda *_: submit("red"))
    assert len(j.charter.tools) == 5 and "small" not in json.dumps(charter_document(j.charter))
    assert replace(j.charter, tools=j.charter.tools[:-1]).fingerprint != j.charter.fingerprint


def test_another_model_keeps_the_outbox_and_asks_no_decided_item_again(tmp_path):
    asked = []

    def at(tier):
        convos = ScriptedConversations(lambda *_: asked.append(tier.model) or submit("red"))
        return paid(convos, model=f"{tier.model}-answered")

    def pick_at(model, things):
        tier = Tier("scripted", model, "high")
        return Pick(Spawned(at(tier), tier, None, at, LADDER), LIBRARY,
                    AttemptLog(tmp_path, "pick", Where("test", "pick"), echo=lambda _: None), Registry(),
                    store=tmp_path / "pick", things=things)
    first = pick_at("small", ("a",))
    assert first.run() == 1
    later = pick_at("other", ("a", "b"))
    assert later.charter.fingerprint == first.charter.fingerprint
    assert later.run() == 1 and asked == ["small", "other"]
    a, b = active_outbox(tmp_path / "pick").records()
    assert (a.item, a.tier["model"], a.answered) == ("a", "small", "small-answered")
    assert (b.item, b.tier["model"], b.answered) == ("b", "other", "other-answered")


def test_a_spend_cap_stops_the_job_after_logging_the_attempt(tmp_path):
    budget = Budget("apps.replace.budget", 100000, spend=5)
    j = job_of(Pick, tmp_path, budget=budget, things=("a", "b"), usage={"input": 4, "output": 4})
    with pytest.raises(OverBudget, match="spendCap is 5"):
        j.run()
    assert len(logged(tmp_path, "pick")) == 1


def test_one_command_shares_one_spend_count_across_the_job_its_reviewer_and_cache_tokens(tmp_path):
    def answer(model, task, *_):
        return {"tool": "verdict", "args": {"verdict": "accept", "reason": "ok"}} if task.name == "review" else submit("red")
    budget = Budget("apps.replace.budget", 10**6, spend=150)
    usage = {"input": 10, "output": 10, "cacheRead": 30, "cacheWrite": 30, "costUsd": 0.25}
    s = spawned(answer, budget, usage)
    registry = Registry()
    reviewer = ReviewJob(s.at(next_tier(s.tier, s.ladder)), LIBRARY,
                         AttemptLog(tmp_path, "review", Where("test", "review"), echo=lambda _: None), registry)
    j = Pick(s, LIBRARY, AttemptLog(tmp_path, "pick", Where("test", "pick"), echo=lambda _: None), registry,
             store=tmp_path / "pick", reviewer=reviewer)
    # the reviewer's 80 cached and uncached tokens, then the job's 80 on the same count, pass 150
    with pytest.raises(OverBudget, match=r"used 160 tokens \(\$0.5000"):
        j.run()
    assert budget.used == 160 and len(logged(tmp_path, "review")) == len(logged(tmp_path, "pick")) == 1
    assert active_outbox(tmp_path / "pick").records() == []


def test_a_failure_past_the_cap_raises_the_failure_not_the_cap(tmp_path):
    def answer(model, task, session, turn):
        if turn == 1:
            return {"tool": "list_groups", "args": {}}
        raise AgentFailed("claude_cli_failed", "usage limit")
    j = job_of(Pick, tmp_path, answer, budget=Budget("apps.replace.budget", 100000, spend=5), usage={"input": 9})
    with pytest.raises(AgentFailed, match="usage limit"):
        j.run()
    assert j.spawned.budget.used == 9


def test_next_tier_climbs_models_never_efforts_then_stops():
    ladder = Ladder(("h", "s", "o"))
    assert next_tier(Tier("g", "h", "low"), ladder) == Tier("g", "s", "low")
    assert next_tier(Tier("g", "o", "low"), ladder) is None and next_tier(Tier("g", None, None), Ladder()) is None


def claude_at(answer, model=CLAUDE_MODELS[0]):
    """The claude gateway's ladder on a scripted transport, from `model` at the lowest effort."""
    def at(tier):
        return ScriptedConversations(lambda task, s, t: answer(tier.model, task, s, t))
    tier = Tier("claude", model, "low")
    return Spawned(at(tier), tier, None, at, CLAUDE.ladder)


def test_the_worst_case_is_six_attempts_on_two_models_then_a_person(tmp_path):
    # before the cap: 3 models then 4 more efforts, 7 tiers x 3 attempts = 21
    log = AttemptLog(tmp_path, "pick", Where("test", "pick"), echo=lambda _: None)
    Pick(claude_at(lambda *_: submit("green")), LIBRARY, log, Registry(), ONE, store=tmp_path / "pick").run()
    entries = logged(tmp_path, "pick")
    assert len(entries) == 6
    assert [(e["tier"]["model"], e["tier"]["effort"]) for e in entries] == [(CLAUDE_MODELS[0], "low")] * 3 + [(CLAUDE_MODELS[1], "low")] * 3
    [record] = active_outbox(tmp_path / "pick").records()
    assert record.outcome == "dropped" and record.tier["model"] == CLAUDE_MODELS[1]


def test_a_reviewer_that_never_answers_makes_at_most_six_attempts_of_its_own(tmp_path):
    def answer(model, task, *_):
        return {"tool": "verdict", "args": {"verdict": "maybe", "reason": "?"}} if task.name == "review" else submit("red")
    s, registry = claude_at(answer), Registry()
    reviewer = ReviewJob(s.at(next_tier(s.tier, s.ladder)), LIBRARY,
                         AttemptLog(tmp_path, "review", Where("test", "review"), echo=lambda _: None), registry, ONE)
    Pick(s, LIBRARY, AttemptLog(tmp_path, "pick", Where("test", "pick"), echo=lambda _: None), registry, ONE,
         store=tmp_path / "pick", reviewer=reviewer).run()
    reviews = logged(tmp_path, "review")
    assert [e["tier"]["model"] for e in reviews] == [CLAUDE_MODELS[1]] * 3 + [CLAUDE_MODELS[2]] * 3
    [record] = active_outbox(tmp_path / "pick").records()
    assert "unidentified" in record.decision and len(logged(tmp_path, "pick")) == 1


def test_the_catalogue_reads_wrap_the_views_and_say_a_coded_problem():
    assert '"id"' in LIST_GROUPS.run({}, Context("x", "y")).text
    missing = VIEW_FOR.run({"identifier": "NoSuchAlgorithm"}, Context("x", "y"))
    assert not missing.ok and missing.text.startswith("algorithm_unknown: ")


def test_an_unidentified_record_names_the_reviewer_as_its_decider(tmp_path):
    def answer(model, task, *_):
        return ({"tool": "verdict", "args": {"verdict": "unidentified", "reason": "not visible"}} if task.name == "review"
                else submit("red"))

    def at(tier):
        return paid(ScriptedConversations(lambda task, s, t: answer(tier.model, task, s, t)), model=f"{tier.model}-model")
    small = Tier("scripted", "small", "low")
    s, registry = Spawned(at(small), small, None, at, LADDER), Registry()
    reviewer = ReviewJob(s.at(next_tier(small, LADDER)), LIBRARY,
                         AttemptLog(tmp_path, "review", Where("test", "review"), echo=lambda _: None), registry)
    Pick(s, LIBRARY, AttemptLog(tmp_path, "pick", Where("test", "pick"), echo=lambda _: None), registry,
         store=tmp_path / "pick", reviewer=reviewer).run()
    [record] = active_outbox(tmp_path / "pick").records()
    assert record.decision == {"unidentified": "not visible"} and (record.tier["model"], record.answered) == ("big", "big-model")


def test_a_command_spawns_one_client_per_tier(tmp_path):
    made = []

    def at(tier):
        made.append(tier.model)
        return ScriptedConversations(lambda *_: submit("red"))
    small = Tier("scripted", "small", "low")
    s = Spawned(at(small), small, None, at, LADDER)
    big = next_tier(small, LADDER)
    assert s.at(big) is s.at(big) and s.at(big).at(small) is s and made == ["small", "big"]
