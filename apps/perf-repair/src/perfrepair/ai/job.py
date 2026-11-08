"""Job: the one template of an AI job. candidates -> render -> turns -> checks (in the submit tool) -> review -> repass
-> escalate -> commit -> log. A subclass gives the data; the loop and its log are the base's and cannot be overridden."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Callable, ClassVar

from ..dto.decision import OutboxRecord
from ..dto.event import END, START
from ..dto.prompt import Charter, SystemPrompt, TaskPrompt
from ..log import emit
from ..log.emit import elapsed_ms
from ..validation import require
from ..validation.json_reply import check_reply
from .attempt.escalate import MAX_ESCALATIONS, next_tier
from .attempt.repass import CHECKS, NO_SUBMIT, REVIEW, Reason, Repass
from .log.attempt_log import AttemptLog
from .model.tier import Tier
from .runtime.engine.ask import Answer, Asked, Limits, Turn, ask
from .runtime.engine.events import cost, tokens
from .runtime.engine.outbox import Outbox, activate
from .runtime.gateway.spawn import Spawned, spawned_of
from .runtime.prompt import PromptLibrary
from .tools.catalogue_read import CATALOGUE_READS
from .tools.registry import Registry
from .tools.tool import SUBMIT, Context, Outcome, Tool

# a reviewer's verdicts; unidentified is a success: the item is a person's
ACCEPT, REFUSE, UNIDENTIFIED = "accept", "refuse", "unidentified"
DECIDED, DROPPED, FAILED, REFUSED, INTERRUPTED = "decided", "dropped", "failed", "refused", "interrupted"
SEALED = ("run", "ask_one", "_item", "_attempt", "_review", "_submit", "_entry", "__setattr__")


@dataclass(frozen=True)
class Settled:
    """An item's end: decided (with the reviewer's verdict when one ran), or dropped with its last reason."""
    outcome: str
    decision: dict | None
    reason: Reason | None
    tier: Tier
    answered: str | None
    verdict: str | None = None


class Job:
    name: ClassVar[str]
    prompt: ClassVar[str]
    submit_name: ClassVar[str] = "submit"
    submit_description: ClassVar[str]
    # the submit tool's arguments: the answer's one shape, walked before the checks run
    submit_schema: ClassVar[dict]
    reads: ClassVar[tuple[Tool, ...]] = CATALOGUE_READS

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        overridden = [n for n in SEALED if n in cls.__dict__]
        if overridden:
            raise TypeError(f"{cls.__name__} overrides {', '.join(overridden)}: the template and its log are Job's")

    def __setattr__(self, name, value):
        if name in SEALED:
            raise TypeError(f"{type(self).__name__} sets {name}: the template and its log are Job's")
        super().__setattr__(name, value)

    def __init__(self, spawned: Spawned, library: PromptLibrary, log: AttemptLog, registry: Registry,
                 limits: Limits = Limits(), store: Path | None = None, reviewer: "Job | None" = None):
        # the class-body check misses a later assignment and a parent __init_subclass__ that skips super()
        replaced = [n for n in SEALED if getattr(type(self), n) is not getattr(Job, n)]
        if replaced:
            raise TypeError(f"{type(self).__name__} replaces {', '.join(replaced)}: the template and its log are Job's")
        spawned = spawned_of(spawned)
        self.spawned, self.log, self.registry, self.limits = spawned, log, registry, limits
        self.store, self.reviewer, self.current = store, reviewer, None
        submit = Tool(self.submit_name, self.submit_description, self.submit_schema, SUBMIT, self._submit)
        registry.add(self.name, [*self._reads(), submit])
        surface = registry.surface(self.name)
        base = library.charter(self.prompt, registry.reply_schema(self.name))
        tools = "\n".join(json.dumps(d, sort_keys=True) for d in surface)
        system = SystemPrompt(base.system.name, f"{base.system.text}\nTOOLS (answer with one call: {{\"tool\": name, \"args\": {{...}}}})\n{tools}\n")
        self.charter: Charter = replace(base, system=system, tools=tuple(json.dumps(d, sort_keys=True) for d in surface))

    # what a job gives: its items and how each is shown, checked, decided and kept
    def candidates(self) -> list:
        raise NotImplementedError

    def key(self, item) -> str:
        return item.key

    def label(self, item) -> str:
        return self.key(item)

    def evidence(self, item) -> str | None:
        """A digest of what the item was decided on; a new one asks the item again."""
        return None

    def render(self, item) -> str:
        raise NotImplementedError

    def checks(self, item, args: dict) -> list[str]:
        """Every problem with a submit beyond its schema; none accepts it."""
        return []

    def decide(self, item, args: dict) -> dict:
        """The decision code records from an accepted submit."""
        return dict(args)

    def apply(self, item, record: OutboxRecord) -> None:
        """A committed record into the job's state, on replay and on commit alike."""

    def finish(self) -> None:
        """After the last item: the job's documents."""

    def unidentified(self, item, reason: str) -> dict:
        """The decision a reviewer's unidentified verdict commits."""
        return {"unidentified": reason}

    def reviews(self, item, submitted: dict) -> bool:
        """Whether a reviewer, when the job has one, reads this answer."""
        return True

    def evidence_text(self, item) -> str:
        """What a reviewer reads of the item: by default the message the job sent."""
        return self.render(item)

    def output_text(self, item, submitted: dict) -> str:
        """What a reviewer reads of the answer: by default the decision code would record."""
        return json.dumps(self.decide(item, submitted), sort_keys=True)

    def _reads(self) -> list[Tool]:
        return list(self.reads)

    # the template
    def run(self, limit: int | None = None) -> int:
        """Every pending candidate, each to a committed record; the number committed by this call."""
        self.log.open()
        outbox = activate(self.store, self.charter)[0] if self.store is not None else None
        records = outbox.records() if outbox else []
        items = self.candidates()
        by_key = {self.key(i): i for i in items}
        # a record decided on other evidence is history: its item is pending again
        for r in records:
            if r.item in by_key and r.evidence == self.evidence(by_key[r.item]):
                self.apply(by_key[r.item], r)
        done = {(r.item, r.evidence) for r in records}
        pending = [i for i in items if (self.key(i), self.evidence(i)) not in done]
        w, started = self.log.where, time.monotonic()
        emit(w.stage, w.step, START, kind="model", app=w.app,
             data={"job": self.name, "pending": len(pending) if limit is None else min(len(pending), limit),
                   "committed": len(records), "tier": str(self.spawned.tier)})
        asked = 0
        try:
            for item in pending[:limit]:
                settled = self._item(item)
                record = OutboxRecord(len(records) + 1, self.key(item), DECIDED if settled.decision is not None else DROPPED,
                                      1, 1, settled.decision, () if settled.reason is None else settled.reason.problems,
                                      settled.tier.to_json(), settled.answered, self.evidence(item))
                if outbox is not None:
                    committed = outbox.append(record)
                    require(f"{self.name} record {record.seq}", [] if committed == record else ["reads back different"])
                records.append(record)
                self.apply(item, record)
                asked += 1
        finally:
            emit(w.stage, w.step, END, kind="model", app=w.app, outcome="ok", durationMs=elapsed_ms(started),
                 data={"job": self.name, "asked": asked, "left": len(pending) - asked})
        self.finish()
        return asked

    def ask_one(self, item) -> Settled:
        """One item to its end with no outbox: a reviewer's question."""
        self.log.open()
        return self._item(item)

    def _item(self, item) -> Settled:
        tier, repass, attempt, steps = self.spawned.tier, Repass([]), 0, 0
        while True:
            attempt += 1
            ctx, verdict, reason, decider, turns = Context(self.name, self.key(item)), None, None, None, []
            started = time.monotonic()
            try:
                asked = self._attempt(item, tier, repass.facts(), ctx, turns.append)
                if ctx.submitted is None:
                    source = CHECKS if any(c["kind"] == SUBMIT for c in ctx.calls) else NO_SUBMIT
                    reason = Reason(source, tuple(asked.problems[-3:]) or ("no tool call was accepted",))
                else:
                    reason, verdict, decider = self._review(item, ctx.submitted)
            except BaseException as e:
                # the turns made before the failure are logged and counted; an interrupt is not a provider failure
                outcome = FAILED if isinstance(e, Exception) else INTERRUPTED
                self._entry(item, attempt, tier, Asked(turns=turns), ctx, outcome, None, None, e, elapsed_ms(started))
                raise
            outcome = DECIDED if ctx.submitted is not None and reason is None else REFUSED
            self._entry(item, attempt, tier, asked, ctx, outcome, reason, verdict, None, elapsed_ms(started))
            if self.spawned.budget is not None:
                self.spawned.budget.check()
            if reason is None:
                if verdict and verdict[0] == UNIDENTIFIED:
                    # the reviewer decided the item is a person's: the record names its tier and model
                    return Settled(DECIDED, self.unidentified(item, verdict[1]), None, decider.tier, decider.answered, UNIDENTIFIED)
                return Settled(DECIDED, self.decide(item, ctx.submitted), None, tier, asked.answered, verdict and verdict[0])
            repass.reasons.append(reason)
            if repass.more():
                continue
            # one model up after the repasses, then the item is a person's
            higher = next_tier(tier, self.spawned.ladder) if steps < MAX_ESCALATIONS else None
            if higher is None:
                return Settled(DROPPED, None, reason, tier, asked.answered)
            tier, repass, steps = higher, Repass([]), steps + 1

    def _review(self, item, submitted: dict) -> tuple[Reason | None, tuple[str, str] | None, Settled | None]:
        if self.reviewer is None or not self.reviews(item, submitted):
            return None, None, None
        found = self.reviewer.ask_one(self.reviewer.question(self, item, submitted))
        verdict = (found.decision or {}).get("verdict"), (found.decision or {}).get("reason", "")
        if found.decision is None:
            # a reviewer that never settles leaves the item to a person
            verdict = UNIDENTIFIED, "the reviewer gave no verdict: " + "; ".join(found.reason.problems if found.reason else ())
        if verdict[0] == REFUSE:
            return Reason(REVIEW, (verdict[1],)), verdict, found
        return None, verdict, found

    def _attempt(self, item, tier: Tier, facts: list[str], ctx: Context, on_turn: Callable[[Turn], None]) -> Asked:
        self.current = item
        text = self.render(item)
        if facts:
            text += "\n\nEARLIER ATTEMPTS (fix what each was refused for)\n" + "\n".join(f"  - {f}" for f in facts)
        spawned = self.spawned.at(tier)

        def check(reply: str) -> Answer:
            call, problems = check_reply(reply, self.charter.schema)
            if problems:
                return Answer(None, tuple(problems))
            tool, out = self.registry.call(ctx, call["tool"], call["args"])
            if tool is not None and tool.kind == SUBMIT and out.ok:
                return Answer(out.value)
            return Answer(result=out.text) if out.ok else Answer(None, (out.text,))

        return ask(spawned, self.charter, TaskPrompt(self.prompt, text, self.key(item)), check, self.limits, on_turn)

    def _submit(self, args: dict, ctx: Context) -> Outcome:
        problems = self.checks(self.current, args)
        return Outcome(not problems, "accepted" if not problems else "; ".join(problems), dict(args))

    def _entry(self, item, attempt: int, tier: Tier, asked: Asked, ctx: Context, outcome: str, reason: Reason | None,
               verdict, error: BaseException | None, took: int) -> None:
        used, spent = tokens(asked.turns), cost(asked.turns)
        if self.spawned.budget is not None:
            self.spawned.budget.spent(used, spent)
        self.log.append({"item": self.key(item), "label": self.label(item), "attempt": attempt, "tier": tier.to_json(),
                         "answered": asked.answered, "outcome": outcome, "durationMs": took, "tokens": used,
                         "costUsd": spent, "turns": [_turn(t) for t in asked.turns], "calls": ctx.calls,
                         "submitted": ctx.submitted, **({"reason": reason.to_json()} if reason else {}),
                         **({"review": {"verdict": verdict[0], "reason": verdict[1]}} if verdict else {}),
                         **({"error": str(error) or type(error).__name__} if error else {})})


def _turn(t) -> dict:
    reply = t.reply or {}
    return {"session": t.session, "turn": t.turn, "status": t.status, "problems": list(t.problems),
            "text": reply.get("text"), "durationMs": t.durationMs, "promptTokens": t.promptTokens}

