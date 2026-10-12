"""The grouping loop: until every item is decided, gate, pop, ask fresh conversations, write the outcome.

Per item: up to `sessions` conversations of up to `turns` turns each; the first accepted answer is
written as `assigned`, and an item no conversation answers acceptably is written as `dropped`. The
outbox record is the commit; knowledge, cursor and errors are rebuilt from the outbox after it.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass

from ...dto.grouping import Item, read_items, read_profiles
from ...dto.grouping_state import Knowledge, OutboxRecord
from ...files import read_json, write_json
from ...orchestrate import journal
from ...orchestrate.agent import Conversations
from ...validation.grouping.answer import parse_answer, validate_answer
from .. import gates
from ..catalog.families import Families
from ..paths import GroupingPaths
from ..prompt.render import render, system_prompt
from ..prompt.schema import SCHEMA
from ..state.cursor import cursor
from ..state.knowledge import apply, project
from ..state.outbox import Outbox
from .attempt import attempt


@dataclass(frozen=True)
class Limits:
    turns: int = 3
    sessions: int = 2


def _errors(records: list[OutboxRecord], items: dict[int, Item]) -> str:
    return "".join(json.dumps({"item": r.item, "qualified": items[r.item].qualified, "seq": r.seq,
                               "problems": list(r.problems)}) + "\n" for r in records if r.outcome == "dropped")


def run(paths: GroupingPaths, conversations: Conversations, families: Families | None = None,
        limits: Limits = Limits(), echo=print) -> Knowledge:
    families = families or Families.load()
    raw_items = read_json(paths.items)
    items, profiles = read_items(raw_items), read_profiles(read_json(paths.profiles))
    by_id = {i.id: i for i in items}
    outbox = Outbox(paths.outbox).open()
    records = outbox.records()
    knowledge = project(records, by_id)
    system = system_prompt()

    while True:
        gates.before_pop(items, profiles, records, knowledge, families)
        place = cursor(items, records)
        write_json(paths.knowledge, knowledge.to_json())
        write_json(paths.cursor, place.to_json())
        paths.errors.write_text(_errors(records, by_id))
        if place.next is None:
            return knowledge
        item = gates.after_pop(raw_items["items"][place.next - 1], profiles, families)
        message = render(item, families.by_id[item.family], knowledge, by_id)

        def check(text: str):
            answer, problems = parse_answer(text)
            return answer, problems or validate_answer(answer, item, knowledge, families)

        answer, last, problems = None, None, []
        for session in range(1, limits.sessions + 1):
            result = attempt(conversations.start(system, SCHEMA), message, check, limits.turns, session)
            for t in result.turns:
                journal.append(paths.journal, {"item": item.id, **asdict(t), "problems": list(t.problems)})
                problems += [f"s{t.session}t{t.turn}: {p}" for p in t.problems]
            last = result.turns[-1]
            if result.answer is not None:
                answer = result.answer
                break

        record = OutboxRecord(len(records) + 1, item.id, "assigned" if answer else "dropped", last.session, last.turn,
                              knowledge.version, answer, () if answer else tuple(problems))
        written = outbox.append(record)
        apply(knowledge, record, item)
        records.append(record)
        gates.after_write(record, OutboxRecord.from_json(json.loads(written.read_text())), records, knowledge, items,
                          families)
        echo(f"item {item.id} {item.qualified}: {record.outcome}"
             + (f" -> {answer.target}" if answer else f" ({len(problems)} problems)")
             + f" [session {last.session}, turn {last.turn}]")
