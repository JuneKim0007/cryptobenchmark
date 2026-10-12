"""The decision engine: until every item of a kind is decided, gate, pop, ask, commit, project.

  A  before pop:   the state is valid and is the projection of the outbox
  B  after pop:    the item is whole (kind.admit)
  C  every answer: the kind's check
  commit:          the outbox record, durable and exclusive, read back from disk
  D  after commit: the new state is valid
The outbox is the only commit; projections (kind.write, errors.jsonl) are rewritten from it every item,
so a crash anywhere loses at most the answer being committed. `limit` decides at most that many items in
this call; the next call resumes.
"""
from __future__ import annotations

import json
from pathlib import Path

from ...dto.decision import OutboxRecord
from ...validation import require
from .. import journal
from ..agent import Conversations
from .ask import Limits, ask
from .kind import DecisionKind, project
from .outbox import Outbox


def _errors(kind: DecisionKind, records: list[OutboxRecord], by_key: dict) -> str:
    return "".join(json.dumps({"item": r.item, "label": kind.label(by_key[r.item]), "seq": r.seq,
                               "problems": list(r.problems)}) + "\n" for r in records if r.outcome == "dropped")


def decide(kind: DecisionKind, conversations: Conversations, root: Path, limits: Limits = Limits(),
           limit: int | None = None, echo=print):
    root = Path(root)
    items = kind.items()
    by_key = {i.key: i for i in items}
    outbox = Outbox(root / "outbox").open()
    records = outbox.records()
    state = project(kind, records)
    decided = 0
    while True:
        require(kind.name, kind.validate(state, records))
        kind.write(state, records)
        (root / "errors.jsonl").write_text(_errors(kind, records, by_key))
        done = {r.item for r in records}
        item = next((i for i in items if i.key not in done), None)
        if item is None or (limit is not None and decided == limit):
            return state
        require(f"{kind.name} item {item.key}", kind.admit(item))
        asked = ask(conversations, kind.system, kind.schema, kind.render(item, state),
                    lambda text: kind.check(item, text, state), limits,
                    lambda turn: journal.append(root / "journal.jsonl", {"item": item.key, **turn.to_json()}))
        accepted = asked.decision is not None
        record = OutboxRecord(len(records) + 1, item.key, "decided" if accepted else "dropped", asked.last.session,
                              asked.last.turn, asked.decision, () if accepted else tuple(asked.problems))
        committed = outbox.append(record)
        require(f"{kind.name} record {record.seq}", [] if committed == record else ["reads back different"])
        kind.apply(state, item, committed)
        records.append(committed)
        decided += 1
        require(kind.name, kind.validate(state, records))
        echo(f"{kind.name} {kind.label(item)}: {record.outcome} [session {record.session}, turn {record.turn}]")
