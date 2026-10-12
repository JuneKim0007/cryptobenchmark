"""Pop an item, ask a fresh agent, gate the answer, apply it, record it — until the queue is empty.

Each call carries only the kind's system prompt and the message `render` builds for one item: no
earlier conversation. State, queue and journal are written after every item.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from .. import run_dir
from ..files import write_json
from . import journal
from .agent import Agent, AgentRefused
from .decisions.kind import Checked, DecisionKind
from .queue import ItemQueue


@dataclass(frozen=True)
class RunPaths:
    queue: Path
    state: Path
    journal: Path

    @classmethod
    def under(cls, run: Path, kind: str) -> "RunPaths":
        return cls(Path(run) / f"{kind}.queue.json", run_dir.state(run, kind), run_dir.journal(run, kind))


def _ask(kind: DecisionKind, agent: Agent, item, state, user: str) -> tuple[Checked, dict | None]:
    try:
        reply = agent(kind.prompt, user, kind.schema)
    except AgentRefused as e:
        return Checked(problems=[f"model refused: {e}"]), None
    return kind.validate(item, reply.text, state), {
        "text": reply.text, "model": reply.model, "requestId": reply.requestId, "usage": reply.usage}


def run(kind: DecisionKind, items: list, agent: Agent, state, paths: RunPaths, max_attempts: int = 2,
        echo=print):
    system_sha = hashlib.sha256(kind.prompt.encode()).hexdigest()[:12]
    queue = ItemQueue.open(paths.queue, items)
    step = len(journal.read(paths.journal))
    while (item := queue.peek()) is not None:
        refused: list[str] = []
        for attempt in range(1, max_attempts + 1):
            user = kind.render(item, state, refused or None)
            checked, reply = _ask(kind, agent, item, state, user)
            decision, status = checked.decision, "applied"
            if decision is None and attempt == max_attempts:
                decision, status = kind.fallback(item, checked.problems), "fallback"
            elif decision is None:
                status = "refused"
            entry = {"step": step, "kind": kind.name, "itemId": item.itemId, "attempt": attempt,
                     "status": status, "systemSha": system_sha, "userMessage": user, "reply": reply,
                     "problems": checked.problems, "warnings": checked.warnings}
            if decision is not None:
                entry["decision"] = kind.decision_json(decision)
                entry["effect"] = kind.apply(item, decision, state)
            journal.append(paths.journal, entry)
            step += 1
            if decision is not None:
                break
            refused = checked.problems
        write_json(paths.state, state.to_json())
        queue.done(item.itemId)
        echo(f"{kind.name} {item.itemId}: {status} (attempt {attempt}) {entry.get('effect', '')}")
    return state
