"""Stage: grouping/items.json + profiles.json → GroupingKind on the engine → knowledge, cursor, errors."""
from __future__ import annotations

from ....dto.grouping_state import Knowledge
from ....dto.prompt import TaskPrompt
from ....run_dir import GroupingPaths
from ...runtime.agent import Conversations, ScriptedConversations
from ...runtime.engine.ask import Limits
from ...runtime.engine.decide import decide
from ...runtime.prompt import PromptLibrary
from .kind import GroupingKind, charter


def _dry_run(task: TaskPrompt, *_):
    return {"group": "", "newGroup": {"id": f"dry-{task.item}", "description": "dry run: no model was called"},
            "amend": [], "reason": "dry run"}


DRY_RUN = ScriptedConversations(_dry_run)


def assign(paths: GroupingPaths, conversations: Conversations, library: PromptLibrary, limits: Limits = Limits(),
           limit: int | None = None, echo=print) -> Knowledge:
    knowledge = decide(GroupingKind(paths), charter(library), conversations, paths.root, limits, limit)
    echo(f"{len(knowledge.groups)} groups, {len(knowledge.dropped)} dropped, knowledge version {knowledge.version}")
    return knowledge
