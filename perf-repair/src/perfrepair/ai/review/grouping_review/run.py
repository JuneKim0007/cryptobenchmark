from __future__ import annotations

from ....dto.prompt import Charter, TaskPrompt
from ....files import read_json, write_json
from ...runtime.engine import journal
from ...runtime.agent import Conversations
from ...runtime.engine.ask import Limits, ask
from ...runtime.prompt import PromptLibrary
from ...runtime.prompt.library import CORRECTION
from ....validation.grouping.supervision import parse_review
from ....grouping.paths import GroupingPaths
from ....grouping.report.checks import read_groups
from .render import render
from .schema import SCHEMA

SCHEMA_VERSION = 2
NAME = "review/grouping-review"


def charter(library: PromptLibrary) -> Charter:
    return library.charter(NAME, SCHEMA)


def supervise(paths: GroupingPaths, library: PromptLibrary, conversations: Conversations, limits: Limits = Limits(),
              echo=print) -> dict:
    document, checks = read_groups(paths), read_json(paths.checks)
    used = charter(library)
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
        asked = ask(conversations, used, message, check, limits,
                    lambda turn: journal.append(paths.supervisor_journal, {"family": family, **turn.to_json()}))
        out[family] = ({"status": "reviewed", "findings": asked.decision["findings"], "problems": []}
                       if asked.decision is not None else {"status": "failed", "findings": [], "problems": asked.problems})
        echo(f"supervisor {family}: {out[family]['status']}, {len(out[family]['findings'])} findings")
    result = {"schemaVersion": SCHEMA_VERSION, "charter": used.fingerprint,
              "prompts": {name: str(library.source(name)) for name in (NAME, CORRECTION)}, "families": out}
    write_json(paths.supervisor, result)
    return result
