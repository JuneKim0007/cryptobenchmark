"""Supervisor: one review conversation per family over groups.json; findings only, validated, never applied.

A review is not an outbox decision: it changes no state, so it is asked through the engine's `ask` but
committed as one supervisor.json.
"""
from __future__ import annotations

from ...files import read_json, write_json
from ...orchestrate import journal
from ...orchestrate.agent import Conversations
from ...orchestrate.engine.ask import Limits, ask
from ...validation.grouping.supervision import parse_review
from ..paths import GroupingPaths
from ..report.checks import read_groups
from .render import render, system_prompt
from .schema import SCHEMA

SCHEMA_VERSION = 1


def supervise(paths: GroupingPaths, conversations: Conversations, limits: Limits = Limits(), echo=print) -> dict:
    document, checks = read_groups(paths), read_json(paths.checks)
    system, out = system_prompt(), {}
    for family, description in sorted(document["families"].items()):
        groups = [g for g in document["groups"] if g["family"] == family]
        if not groups:
            continue
        membership = {g["id"]: g["members"] for g in groups}

        def check(text: str):
            findings, problems = parse_review(text, membership)
            return (None if findings is None else {"findings": findings}), problems

        asked = ask(conversations, system, SCHEMA, render(family, description, groups, document["items"], checks["findings"]), check, limits,
                    lambda turn: journal.append(paths.supervisor_journal, {"family": family, **turn.to_json()}))
        out[family] = ({"status": "reviewed", "findings": asked.decision["findings"], "problems": []}
                       if asked.decision is not None else {"status": "failed", "findings": [], "problems": asked.problems})
        echo(f"supervisor {family}: {out[family]['status']}, {len(out[family]['findings'])} findings")
    result = {"schemaVersion": SCHEMA_VERSION, "families": out}
    write_json(paths.supervisor, result)
    return result
