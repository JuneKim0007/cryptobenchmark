from __future__ import annotations

from ...dto.prompt import Charter, TaskPrompt
from ...files import read_json, write_json
from ...orchestrate import journal
from ...orchestrate.agent import Conversations
from ...orchestrate.engine.ask import Limits, ask
from ...orchestrate.prompt import PromptLibrary
from ...validation.grouping.supervision import parse_review
from ..paths import GroupingPaths
from ..report.checks import read_groups
from .render import render
from .schema import SCHEMA

SCHEMA_VERSION = 1
NAME = "grouping-supervise"


def charter(library: PromptLibrary) -> Charter:
    return library.charter(NAME, SCHEMA)


def supervise(paths: GroupingPaths, charter: Charter, conversations: Conversations, limits: Limits = Limits(),
              echo=print) -> dict:
    document, checks = read_groups(paths), read_json(paths.checks)
    out = {}
    for family, description in sorted(document["families"].items()):
        groups = [g for g in document["groups"] if g["family"] == family]
        if not groups:
            continue
        membership = {g["id"]: g["members"] for g in groups}

        def check(text: str):
            findings, problems = parse_review(text, membership)
            return (None if findings is None else {"findings": findings}), problems

        message = TaskPrompt(NAME, render(family, description, groups, document["items"], checks["findings"]), family)
        asked = ask(conversations, charter, message, check, limits,
                    lambda turn: journal.append(paths.supervisor_journal, {"family": family, **turn.to_json()}))
        out[family] = ({"status": "reviewed", "findings": asked.decision["findings"], "problems": []}
                       if asked.decision is not None else {"status": "failed", "findings": [], "problems": asked.problems})
        echo(f"supervisor {family}: {out[family]['status']}, {len(out[family]['findings'])} findings")
    result = {"schemaVersion": SCHEMA_VERSION, "families": out}
    write_json(paths.supervisor, result)
    return result
