"""Stage: grouping/items.json + profiles.json + screen.json → GroupingKind on the engine → knowledge, cursor, errors."""
from __future__ import annotations

from cryptobench.shared.paths import GroupingTree
from ....dto.grouping_state import Knowledge, code_made
from cryptobench.shared.digest.tree import byte_digest
from ....dto.prompt import TaskPrompt
from ...runtime.agent import Conversations, ScriptedConversations
from ...runtime.engine.ask import Limits
from ...runtime.engine.decide import decide
from ...log.where import Where
from ...runtime.prompt import PromptLibrary
from .kind import GroupingKind, charter


def _dry_run(task: TaskPrompt, *_):
    return {"group": "", "newGroup": {"id": f"dry-{byte_digest(task.item.encode())[:12]}", "description": "dry run: no model was called"},
            "amend": [], "reason": "dry run"}


def dry_run() -> ScriptedConversations:
    """The dry-run gateway's stand-in, one per command, so what it records lasts only as long as the command."""
    return ScriptedConversations(_dry_run)


def assign(paths: GroupingTree, conversations: Conversations, library: PromptLibrary, limits: Limits = Limits(),
           limit: int | None = None, echo=print) -> Knowledge:
    kind = GroupingKind(paths)
    knowledge = decide(kind, charter(library), conversations, paths.root, limits, limit, where=Where("grouping", "assign"), device=paths.root.parent)
    coded = sum(code_made(g) for g in knowledge.groups)
    echo(f"{len(knowledge.groups)} groups ({coded} made by code), {len(knowledge.dropped)} dropped, "
         f"knowledge version {knowledge.version}")
    return knowledge
