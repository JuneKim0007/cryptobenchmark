"""Stage: <app>/dossiers.json's broken uses → the upgrade list, or UpgradeKind on the engine for the unlisted → <app>/upgrades.json."""
from __future__ import annotations

from collections import Counter
from pathlib import Path

from .... import run_dir as rd
from ....inputs.table import APPS_UPGRADE
from ...runtime.agent import Conversations, ScriptedConversations
from ...runtime.engine.ask import Limits
from ...runtime.engine.decide import decide
from ...runtime.engine.events import Where
from ...runtime.prompt import PromptLibrary
from .kind import UpgradeKind, charter
from .state import UpgradeState

ROLE = APPS_UPGRADE
DRY_RUN = ScriptedConversations(lambda *_: {"option": "R1", "reason": "dry run: no model was called; the first ranked option"})


def counts(state: UpgradeState) -> str:
    """One line of what the broken uses became."""
    found = Counter(u.status for u in state.rows.values())
    return f"{len(state.rows)} broken uses" + "".join(f", {n} {status}" for status, n in sorted(found.items()))


def upgrade(run_path: Path, app: str, conversations: Conversations, library: PromptLibrary, limits: Limits = Limits(),
            limit: int | None = None, echo=print) -> UpgradeState:
    paths = rd.AppPaths(run_path, app)
    kind = UpgradeKind(app, rd.read_dossiers(paths.dossiers), paths.root)
    state = decide(kind, charter(library, kind.inputs()), conversations, paths.upgrade, limits, limit, echo,
                   Where("repair", "upgrade", app))
    echo(f"{app}: {counts(state)}")
    return state
