"""The kinds that Identify replaces (classify, grouping assign) keep this item loop until then: gates, ask, durable
commit, projections; every attempt goes to log/ai/<kind>.yaml, as Job's do."""
from __future__ import annotations

import time
from pathlib import Path

from ....dto.decision import OutboxRecord
from ....dto.event import END, START
from ....dto.prompt import Charter
from ....files import write_json
from ....log import emit
from ....log.emit import elapsed_ms
from ....validation import require
from ...log.attempt_log import AttemptLog
from ...log.where import Where
from ...model.tier import Tier
from ..agent import Conversations
from .ask import Asked, Limits, ask
from .events import cost, tokens
from .kind import DecisionKind, admit_problems, evidence_of, narrower_of, project
from .outbox import Outbox, activate

NO_TIER = Tier("none")


def _started(where: Where, outbox: Outbox, replaced: Outbox | None, records: list, pending: list, tier, limit) -> None:
    done = {r.item for r in records}
    todo = sum(1 for i in pending if i.key not in done)
    emit(where.stage, where.step, START, kind="model", app=where.app,
         outcome="rotated" if replaced is not None else ("resumed" if records else "opened"),
         data={"outbox": outbox.fingerprint, "replaced": replaced and replaced.fingerprint, "committed": len(records),
               "pending": todo if limit is None else min(todo, limit), "tier": str(tier)})


def _commit(kind: DecisionKind, item, asked: Asked, records: list, outbox: Outbox, tier: Tier) -> OutboxRecord:
    accepted = asked.decision is not None
    record = OutboxRecord(len(records) + 1, item.key, "decided" if accepted else "dropped", asked.last.session,
                          asked.last.turn, asked.decision, () if accepted else tuple(asked.problems), tier.to_json(),
                          asked.answered, evidence_of(kind, item))
    committed = outbox.append(record)
    require(f"{kind.name} record {record.seq}", [] if committed == record else ["reads back different"])
    return committed


def _logged(log: AttemptLog, kind: DecisionKind, item, asked: Asked, record: OutboxRecord, tier: Tier, took: int) -> None:
    log.append({"item": item.key, "label": kind.label(item), "attempt": 1, "tier": tier.to_json(), "answered": asked.answered,
                "outcome": record.outcome, "durationMs": took, "tokens": tokens(asked.turns), "costUsd": cost(asked.turns),
                "turns": [{"session": t.session, "turn": t.turn, "status": t.status, "problems": list(t.problems),
                           "text": (t.reply or {}).get("text"), "promptTokens": t.promptTokens} for t in asked.turns],
                **({"narrowedFrom": asked.narrowedFrom} if asked.narrowedFrom else {}),
                **({"reason": {"source": "no_submit", "problems": list(record.problems)}} if record.problems else {})})


def decide(kind: DecisionKind, charter: Charter, conversations: Conversations, root: Path, limits: Limits = Limits(),
           limit: int | None = None, echo=print, where: Where | None = None, device: Path | None = None):
    """device: where log/ai/<kind>.yaml lives; the kind's own folder when none is given."""
    root, where = Path(root), where or Where(kind.name, "decide")
    tier = getattr(conversations, "tier", NO_TIER)
    log = AttemptLog(device or root, kind.name, where, echo).open()
    pending = kind.pending()
    outbox, replaced = activate(root, charter)
    records = outbox.records()
    if replaced is not None:
        echo(f"charter changed: outbox {replaced.fingerprint} → {outbox.fingerprint} "
             f"({len(replaced.records())} records kept in {replaced.fingerprint}, {len(records)} resumed)")
    _started(where, outbox, replaced, records, pending, tier, limit)
    state, started, counts = project(kind, records), time.monotonic(), {"decided": 0, "dropped": 0}
    while True:
        require(kind.name, kind.validate(state, records))
        for file, document in kind.documents(state, records).items():
            write_json(file, document)
        done = {r.item for r in records}
        left = [i for i in pending if i.key not in done]
        if not left or (limit is not None and sum(counts.values()) == limit):
            emit(where.stage, where.step, END, kind="model", app=where.app, outcome="ok", durationMs=elapsed_ms(started),
                 data={"counts": {**counts, "committed": len(records), "left": len(left)}, "outbox": outbox.fingerprint})
            return state
        item = left[0]
        require(f"{kind.name} item {item.key}", admit_problems(kind, item))
        asked_at = time.monotonic()
        asked = ask(conversations, charter, kind.render(item, state), lambda text: kind.check(item, text, state), limits,
                    narrow=narrower_of(kind, item, state))
        committed = _commit(kind, item, asked, records, outbox, tier)
        _logged(log, kind, item, asked, committed, tier, elapsed_ms(asked_at))
        kind.apply(state, item, committed)
        records.append(committed)
        counts[committed.outcome] += 1
        require(kind.name, kind.validate(state, records))
