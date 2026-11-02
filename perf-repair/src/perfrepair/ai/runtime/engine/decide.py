from __future__ import annotations

import json
import logging
from pathlib import Path

from ....dto.decision import AgentIdentity, OutboxRecord
from ....dto.prompt import Charter
from ....validation import require
from . import journal
from ..agent import Conversations
from .ask import Limits, ask
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


def decide(kind: DecisionKind, charter: Charter, conversations: Conversations, root: Path, limits: Limits = Limits(),
           limit: int | None = None, echo=print):
    root = Path(root)
    by_key = {i.key: i for i in kind.items()}
    pending = kind.pending()
    outbox, replaced = activate(root, charter)
    records = outbox.records()
    if replaced is not None:
        echo(f"charter changed: outbox {replaced.fingerprint} → {outbox.fingerprint} "
             f"({len(replaced.records())} records kept in {replaced.fingerprint}, {len(records)} resumed)")
    agent = getattr(conversations, "identity", AgentIdentity())
    _warn_if_mixed(outbox, records, agent, pending)
    state = project(kind, records)
    decided = 0
    while True:
        require(kind.name, kind.validate(state, records))
        kind.write(state, records)
        (root / "errors.jsonl").write_text(_errors(kind, records, by_key))
        done = {r.item for r in records}
        item = next((i for i in pending if i.key not in done), None)
        if item is None or (limit is not None and decided == limit):
            return state
        require(f"{kind.name} item {item.key}", kind.admit(item))
        asked = ask(conversations, charter, kind.render(item, state),
                    lambda text: kind.check(item, text, state), limits,
                    lambda turn: journal.append(root / "journal.jsonl", {"charter": outbox.fingerprint, "item": item.key, **turn.to_json()}))
        accepted = asked.decision is not None
        record = OutboxRecord(len(records) + 1, item.key, "decided" if accepted else "dropped", asked.last.session,
                              asked.last.turn, asked.decision, () if accepted else tuple(asked.problems), agent)
        committed = outbox.append(record)
        require(f"{kind.name} record {record.seq}", [] if committed == record else ["reads back different"])
        kind.apply(state, item, committed)
        records.append(committed)
        decided += 1
        require(kind.name, kind.validate(state, records))
        echo(f"{kind.name} {kind.label(item)}: {record.outcome} [session {record.session}, turn {record.turn}]")
