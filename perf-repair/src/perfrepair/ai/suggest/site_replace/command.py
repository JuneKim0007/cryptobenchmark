"""Stage: apps/<app>/dossiers.json → SiteReplaceKind on the engine → apps/<app>/replacements.json."""
from __future__ import annotations

from pathlib import Path

from .... import run_dir as rd
from ....files import read_json
from ....validation import require
from ...runtime.agent import Conversations, ScriptedConversations
from ...runtime.engine.ask import Limits
from ...runtime.engine.decide import decide
from ...runtime.prompt import PromptLibrary
from .kind import SiteReplaceKind, charter
from .state import Replacements

DRY_RUN = ScriptedConversations(lambda *_: {"decision": "keep", "option": "", "edits": [], "risks": [],
                                            "reason": "dry run: no model was called"})


def replace(run_path: Path, app: str, conversations: Conversations, library: PromptLibrary, limits: Limits = Limits(),
            limit: int | None = None, echo=print) -> Replacements:
    paths = rd.AppPaths(run_path, app)
    kind = SiteReplaceKind(app, read_json(paths.dossiers), paths.root)
    require(str(paths.dossiers), kind.problems)
    state = decide(kind, charter(library), conversations, paths.replace, limits, limit, echo)
    counts: dict[str, int] = {}
    for scope, r in state.replacements.items():
        key = f"{r.decision} ({state.sources[scope]})"
        counts[key] = counts.get(key, 0) + 1
    echo(f"{app}: {len(kind.dossiers)} sites, {len(kind.items())} asked, {counts}")
    return state
