"""Stage: <app>/gaps.json → ScopeCompleteKind on the engine → completed.json, and the answers applied to scopes.json."""
from __future__ import annotations

import argparse
from pathlib import Path

from .... import run_dir as rd
from ....config.load import Loaded
from ....dto.gaps import UNKNOWN_CHOICE, UNKNOWN_ORIGIN, read_gaps
from ....dto.lifecycle import MODEL_PREFIX
from ....dto.prompt import TaskPrompt
from ....dto.site import Scope
from ....files import read_json, write_json
from ....inputs.table import APPS_COMPLETE
from ....log import step
from ....scope.complete import apply_answers
from ....validation import require
from ....validation.app import validate_scopes
from ....validation.gaps import validate_gaps
from ...runtime.agent import Conversations, ScriptedConversations
from ...runtime.engine.ask import Limits
from ...runtime.engine.decide import decide
from ...runtime.engine.events import Where
from ...runtime.gateway.spawn import spawn
from ...runtime.prompt import PromptLibrary
from .kind import ScopeCompleteKind, charter
from .render import gap_ids
from .state import Completed


def _dry_run(task: TaskPrompt, *_):
    return {"answers": [{"gap": g, "choice": UNKNOWN_CHOICE, "origin": UNKNOWN_ORIGIN} for g in gap_ids(task.text)]}


DRY_RUN = ScriptedConversations(_dry_run)
ROLE = APPS_COMPLETE


def conversations_for(args: argparse.Namespace, settings: Loaded) -> Conversations:
    """This role's conversations whichever command called it; a gateway named there reaches it, other keys resolve by role."""
    return spawn(argparse.Namespace(**{**vars(args), "agent_role": ROLE}), settings, DRY_RUN)


def _applied(doc: dict, kind: ScopeCompleteKind, state: Completed, source: str) -> tuple[dict, int]:
    entries, out, changed = {e.key: e for e in kind.entries}, [], 0
    for raw in doc["scopes"]:
        s = Scope.from_json(raw)
        done = apply_answers(s, entries[s.id], state.answers[s.id], source) if s.id in state.answers else s
        changed += done != s
        out.append(done.to_json())
    return {**doc, "scopes": out}, changed


def _other_charter(doc: dict, source: str) -> str | None:
    """Answers only grow within one outbox; a scope completed under another needs the static scopes back first."""
    for s in map(Scope.from_json, doc["scopes"]):
        lc = s.lifecycle
        held = [r.completed for r in lc.requirements if r.completed] + ([lc.use] if lc.use else []) if lc is not None else []
        if any(c.by_model and c.source != source for c in held):
            return s.id
    return None


def scope_complete(run_path: Path, app: str, conversations: Conversations, library: PromptLibrary,
                   limits: Limits = Limits(), limit: int | None = None, echo=print) -> Completed:
    paths = rd.AppPaths(run_path, app)
    doc, gaps = read_json(paths.scopes), read_json(paths.gaps)
    require(rd.GAPS, validate_gaps(gaps, doc))
    kind = ScopeCompleteKind(app, read_gaps(gaps), paths.root)
    fixed = charter(library, kind.inputs)
    source = f"{MODEL_PREFIX}{fixed.fingerprint}"
    other = _other_charter(doc, source)
    if other is not None:
        raise ValueError(f"scopes_completed: scope {other} holds answers of another outbox; rerun perfrepair.app first")
    state = decide(kind, fixed, conversations, paths.complete, limits, limit, echo, Where("app", "scope-complete", app))
    with step("app", "scope-apply", app=app) as s:
        completed, changed = _applied(doc, kind, state, source)
        require(rd.SCOPES, validate_scopes(completed))
        write_json(paths.scopes, completed)
        s.count(asked=len(kind.items()), answered=len(state.answers), dropped=len(state.dropped), scopes=changed)
        s.wrote(paths.scopes)
    echo(f"{app}: {len(kind.items())} scopes with candidates of {len(kind.entries)} with gaps, {len(state.answers)} answered, "
         f"{changed} scopes completed")
    return state
