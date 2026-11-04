"""Stage: groups.json + checks.json → GroupingReviewKind on the engine → supervisor.json, its outbox and journal under grouping/review."""
from __future__ import annotations

from ....run_dir import GroupingPaths
from ...runtime.agent import Conversations, ScriptedConversations
from ...runtime.engine.ask import Limits
from ...runtime.engine.decide import decide
from ...runtime.engine.events import Where
from ...runtime.prompt import PromptLibrary
from .kind import GroupingReviewKind

DRY_RUN = ScriptedConversations(lambda *_: {"findings": []})


def review(paths: GroupingPaths, conversations: Conversations, library: PromptLibrary, limits: Limits = Limits(),
           echo=print) -> dict:
    kind = GroupingReviewKind(paths, library)
    return kind.document(decide(kind, kind.charter, conversations, paths.review, limits, echo=echo,
                                where=Where("grouping", "review")))
