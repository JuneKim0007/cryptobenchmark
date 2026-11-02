from __future__ import annotations

import json
import logging
import time
from pathlib import Path

from ....dto.decision import AgentIdentity, OutboxRecord
from ....dto.event import END, START
from ....dto.prompt import Charter
from ....log import emit
from ....log.emit import elapsed_ms
from ....validation import require
from . import journal
from ..agent import Conversations
from .ask import Limits, ask
from .events import TurnEvents, Where
from .kind import DecisionKind, project
from .outbox import Outbox, activate

LOG = logging.getLogger(__name__)


def _errors(kind: DecisionKind, records: list[OutboxRecord], by_key: dict) -> str:
    return "".join(json.dumps({"item": r.item, "label": kind.label(by_key[r.item]), "seq": r.seq,
                               "problems": list(r.problems)}) + "\n" for r in records if r.outcome == "dropped")


def _warn_if_mixed(outbox: Outbox, records: list[OutboxRecord], now: AgentIdentity, pending: list) -> None:
    earlier = sorted({str(r.agent) for r in records if r.agent not in (now, AgentIdentity())})
    asked = {r.item for r in records}
    if earlier and now != AgentIdentity() and any(i.key not in asked for i in pending):
        LOG.warning("mixed_agents: outbox %s holds answers from %s, now asking %s", outbox.fingerprint, ", ".join(earlier), now)


def _started(where: Where, outbox: Outbox, replaced: Outbox | None, records: list, pending: list, agent, limit) -> None:
    done = {r.item for r in records}
    todo = sum(1 for i in pending if i.key not in done)
    emit(where.stage, where.step, START, kind="model", app=where.app,
         outcome="rotated" if replaced is not None else ("resumed" if records else "opened"),
         data={"outbox": outbox.fingerprint, "replaced": replaced and replaced.fingerprint, "committed": len(records),
               "pending": todo if limit is None else min(todo, limit), "agent": str(agent)})


def decide(kind: DecisionKind, charter: Charter, conversations: Conversations, root: Path, limits: Limits = Limits(),
           limit: int | None = None, echo=print, where: Where | None = None):
    root, where = Path(root), where or Where(kind.name, "decide")
    by_key = {i.key: i for i in kind.items()}
    pending = kind.pending()
    outbox, replaced = activate(root, charter)
    records = outbox.records()
    if replaced is not None:
        echo(f"charter changed: outbox {replaced.fingerprint} → {outbox.fingerprint} "
             f"({len(replaced.records())} records kept in {replaced.fingerprint}, {len(records)} resumed)")
    agent = getattr(conversations, "identity", AgentIdentity())
    _warn_if_mixed(outbox, records, agent, pending)
    _started(where, outbox, replaced, records, pending, agent, limit)
    events = TurnEvents(where, root / "journal.jsonl", journal.count(root / "journal.jsonl"), outbox.fingerprint)
    state, started = project(kind, records), time.monotonic()
    decided, counts = 0, {"decided": 0, "dropped": 0}
    while True:
        require(kind.name, kind.validate(state, records))
        kind.write(state, records)
        (root / "errors.jsonl").write_text(_errors(kind, records, by_key))
        done = {r.item for r in records}
        item = next((i for i in pending if i.key not in done), None)
        if item is None or (limit is not None and decided == limit):
            left = sum(1 for i in pending if i.key not in done)
            emit(where.stage, where.step, END, kind="model", app=where.app, outcome="ok", durationMs=elapsed_ms(started),
                 data={"counts": {**counts, "committed": len(records), "left": left}, "outbox": outbox.fingerprint})
            return state
        require(f"{kind.name} item {item.key}", kind.admit(item))

        def on_turn(turn):
            journal.append(root / "journal.jsonl", {"charter": outbox.fingerprint, "item": item.key, **turn.to_json()})
            events.turn(item.key, turn)

        asked = ask(conversations, charter, kind.render(item, state), lambda text: kind.check(item, text, state), limits,
                    on_turn)
        accepted = asked.decision is not None
        record = OutboxRecord(len(records) + 1, item.key, "decided" if accepted else "dropped", asked.last.session,
                              asked.last.turn, asked.decision, () if accepted else tuple(asked.problems), agent)
        committed = outbox.append(record)
        require(f"{kind.name} record {record.seq}", [] if committed == record else ["reads back different"])
        events.decision(item.key, kind.label(item), record.outcome, asked, outbox.path(record.seq))
        kind.apply(state, item, committed)
        records.append(committed)
        decided += 1
        counts[record.outcome] += 1
        require(kind.name, kind.validate(state, records))
        echo(f"{kind.name} {kind.label(item)}: {record.outcome} [session {record.session}, turn {record.turn}]")
