"""Stage: groups.json + checks.json → one supervisor review per family → supervisor.json."""
from __future__ import annotations

from ....grouping.paths import GroupingPaths
from ...runtime.agent import Conversations, ScriptedConversations
from ...runtime.prompt import PromptLibrary
from .run import charter, supervise

DRY_RUN = ScriptedConversations(lambda *_: {"findings": []})


def review(paths: GroupingPaths, conversations: Conversations, library: PromptLibrary) -> dict:
    used = charter(library)
    return supervise(paths, used, conversations, library.provenance(used))
