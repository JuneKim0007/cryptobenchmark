"""Stage: grouping/items.json + profiles.json + screen.json → GroupingKind on the engine → knowledge, cursor, errors."""
from __future__ import annotations

from ....dto.grouping_state import Knowledge, code_made
from ....dto.prompt import TaskPrompt
from ....run_dir import GroupingPaths
from ...runtime.agent import Conversations, ScriptedConversations
from ...runtime.engine.ask import Limits
from ...runtime.engine.decide import decide
from ...runtime.engine.events import Where
from ...runtime.prompt import PromptLibrary
from .kind import GroupingKind, charter


def _dry_run(task: TaskPrompt, *_):
    return {"group": "", "newGroup": {"id": f"dry-{task.item}", "description": "dry run: no model was called"},
            "amend": [], "reason": "dry run"}


DRY_RUN = ScriptedConversations(_dry_run)


def assign(paths: GroupingPaths, conversations: Conversations, library: PromptLibrary, limits: Limits = Limits(),
           limit: int | None = None, echo=print) -> Knowledge:
    kind = GroupingKind(paths)
    knowledge = decide(kind, charter(library, kind.inputs), conversations, paths.root, limits, limit,
                       where=Where("grouping", "assign"))
    coded = sum(code_made(g) for g in knowledge.groups)
    echo(f"{len(knowledge.groups)} groups ({coded} made by code), {len(knowledge.dropped)} dropped, "
         f"knowledge version {knowledge.version}")
    return knowledge
