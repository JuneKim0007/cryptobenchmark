"""Stage step of grouping build: unknown items in batches → ClassifyKind on the engine → reviewed verdicts."""
from __future__ import annotations

from dataclasses import dataclass

import yaml

from ....dto.classify import UNSURE, Batch, batch_ids, batches_document, read_batches
from ....dto.prompt import TaskPrompt
from ....dto.screen import Verdict
from ....files import read_json, write_json, write_text
from ....run_dir import GroupingPaths
from ...runtime.agent import Conversations, ScriptedConversations
from ...runtime.engine.ask import Limits
from ...runtime.engine.decide import decide
from ...runtime.engine.events import Where
from ...runtime.engine.tracking import role_run
from ...runtime.prompt import PromptLibrary
from .kind import ClassifyKind, charter
from .state import candidates, reviewed


def _dry_run(task: TaskPrompt, *_):
    return {"answers": [{"id": i, "answer": UNSURE, "reason": "dry run: no model was called"}
                        for i in batch_ids(task.item)]}


DRY_RUN = ScriptedConversations(_dry_run)


@dataclass(frozen=True)
class Reviewer:
    conversations: Conversations
    library: PromptLibrary
    limits: Limits = Limits()


def classify(paths: GroupingPaths, batches: list[Batch], verdicts: dict[int, Verdict], reviewer: Reviewer,
             echo=print) -> tuple[dict[int, Verdict], str]:
    """The verdicts with the model's answers applied, and the outbox fingerprint they are sourced by."""
    paths.classify.mkdir(parents=True, exist_ok=True)
    write_json(paths.classify_batches, batches_document(batches))
    with role_run("screening.classify", paths.root.parent):
        # the file, not the build's memory: what the journal names is what the model is shown
        batches = read_batches(read_json(paths.classify_batches))
        kind = ClassifyKind(batches, paths)
        fixed = charter(reviewer.library, kind.inputs)
        state = decide(kind, fixed, reviewer.conversations, paths.classify, reviewer.limits, echo=echo,
                       where=Where("screening", "classify"))
        proposals = candidates(state, batches, fixed.fingerprint)
        write_text(paths.registry_candidates, yaml.safe_dump(proposals, sort_keys=False))
    counts: dict[str, int] = {}
    for a in state.answers.values():
        counts[a.answer] = counts.get(a.answer, 0) + 1
    echo(f"classify: {sum(len(b.members) for b in batches)} unknown items in {len(batches)} batches, {counts}; "
         f"{len(proposals['candidates'])} candidates -> {paths.registry_candidates}")
    return reviewed(verdicts, state, fixed.fingerprint), fixed.fingerprint
