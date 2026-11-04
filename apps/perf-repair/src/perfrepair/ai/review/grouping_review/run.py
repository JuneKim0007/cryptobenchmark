from __future__ import annotations

from collections import Counter

from ....dto.charter import charter_document
from ....dto.grouping_state import code_made
from ....dto.prompt import Charter, TaskPrompt
from ....files import read_json, write_json
from ....log import step
from ...runtime.engine import journal
from ...runtime.agent import Conversations
from ...runtime.engine.ask import Limits, ask
from ...runtime.engine.events import TurnEvents, Where
from ...runtime.prompt import PromptLibrary
from ....validation.review.grouping_review import parse_review
from ....run_dir import GroupingPaths
from ....validation.grouping.output import read_groups
from .render import render
from .schema import SCHEMA

SCHEMA_VERSION = 2
NAME = "review/grouping-review"


def charter(library: PromptLibrary) -> Charter:
    return library.charter(NAME, SCHEMA)


def _review(paths: GroupingPaths, charter: Charter, conversations: Conversations, limits: Limits, events: TurnEvents,
            document: dict, checks: dict, family: str, groups: list[dict]) -> dict:
    membership = {g["id"]: g["members"] for g in groups}

    def check(text: str):
        findings, problems = parse_review(text, membership)
        return (None if findings is None else {"findings": findings}), problems

    def on_turn(turn):
        journal.append(paths.supervisor_journal, {"charter": charter.fingerprint, "family": family, **turn.to_json()})
        events.turn(family, turn)

    message = TaskPrompt(NAME, render(family, document["families"][family], groups, document["items"], checks["findings"]),
                         family)
    asked = ask(conversations, charter, message, check, limits, on_turn)
    result = ({"status": "reviewed", "findings": asked.decision["findings"], "problems": []}
              if asked.decision is not None else {"status": "failed", "findings": [], "problems": asked.problems})
    events.decision(family, family, result["status"], asked, None)
    return result


def supervise(paths: GroupingPaths, charter: Charter, conversations: Conversations, prompts: dict[str, str],
              limits: Limits = Limits(), echo=print) -> dict:
    """prompts: each of the charter's prompt names to the file it was read from, recorded in supervisor.json."""
    if set(prompts) != set(charter.prompts):
        raise ValueError(f"prompts name {sorted(prompts)}, the charter was built from {sorted(charter.prompts)}")
    document, checks = read_groups(paths), read_json(paths.checks)
    events = TurnEvents(Where("grouping", "review"), paths.supervisor_journal, journal.count(paths.supervisor_journal),
                        charter.fingerprint)
    wanted = {f: [g for g in document["groups"] if g["family"] == f and not code_made(g["id"])]
              for f in sorted(document["families"])}
    wanted = {f: groups for f, groups in wanted.items() if groups}
    out = {}
    with step("grouping", "review", kind="model", data={"pending": len(wanted), "outbox": charter.fingerprint}) as s:
        for family, groups in wanted.items():
            out[family] = _review(paths, charter, conversations, limits, events, document, checks, family, groups)
            echo(f"supervisor {family}: {out[family]['status']}, {len(out[family]['findings'])} findings")
        s.count(**Counter(r["status"] for r in out.values()))
    result = {"schemaVersion": SCHEMA_VERSION, "charter": charter.fingerprint, "prompts": prompts, "families": out}
    # no outbox: the charter of this review sits beside the one supervisor.json it made
    write_json(paths.supervisor_charter, charter_document(charter))
    write_json(paths.supervisor, result)
    return result
