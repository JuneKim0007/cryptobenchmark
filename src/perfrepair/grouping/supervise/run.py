"""Supervisor: one review conversation per family over groups.json; findings only, validated, never applied."""
from __future__ import annotations

from ...files import read_json, write_json
from ...orchestrate import journal
from ...orchestrate.agent import Conversations
from ...validation.grouping.supervision import parse_review
from ..loop.attempt import attempt
from ..loop.run import Limits
from ..paths import GroupingPaths
from .render import render, system_prompt
from .schema import SCHEMA


def supervise(paths: GroupingPaths, conversations: Conversations, limits: Limits = Limits(), echo=print) -> dict:
    document, checks = read_json(paths.groups), read_json(paths.checks)
    system, out = system_prompt(), {}
    for family, description in sorted(document["families"].items()):
        groups = [g for g in document["groups"] if g["family"] == family]
        if not groups:
            continue
        membership = {g["id"]: g["members"] for g in groups}
        message = render(family, description, groups, document["items"], checks["findings"])

        def check(text: str):
            findings, problems = parse_review(text, membership)
            return (None if findings is None else findings), problems

        result, problems = None, []
        for session in range(1, limits.sessions + 1):
            done = attempt(conversations.start(system, SCHEMA), message, check, limits.turns, session)
            for t in done.turns:
                journal.append(paths.supervisor_journal,
                               {"family": family, "session": t.session, "turn": t.turn, "status": t.status,
                                "problems": list(t.problems), "reply": t.reply})
                problems += [f"s{t.session}t{t.turn}: {p}" for p in t.problems]
            if done.answer is not None:
                result = done.answer
                break
        out[family] = ({"status": "reviewed", "findings": result, "problems": []} if result is not None
                       else {"status": "failed", "findings": [], "problems": problems})
        echo(f"supervisor {family}: {out[family]['status']}, {len(out[family]['findings'])} findings")
    document = {"schemaVersion": 1, "families": out}
    write_json(paths.supervisor, document)
    return document
