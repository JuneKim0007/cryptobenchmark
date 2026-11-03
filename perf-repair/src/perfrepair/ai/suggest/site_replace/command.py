"""Stage: <app>/dossiers.json → SiteReplaceKind on the engine → <app>/replacements.json."""
from __future__ import annotations

from dataclasses import replace as replace_record
from pathlib import Path

from .... import run_dir as rd
from ....files import read_json
from ....validation import require
from ...runtime.agent import Conversations, ScriptedConversations
from ...runtime.engine.ask import Limits
from ...runtime.engine.decide import decide
from ...runtime.engine.events import Where
from ...runtime.engine.kind import project
from ...runtime.engine.outbox import active_outbox, carry
from ...runtime.engine.refresh import kept_inputs, refresh_inputs
from ...runtime.prompt import PromptLibrary
from .kind import SiteReplaceKind, charter
from .state import Replacements

DRY_RUN = ScriptedConversations(lambda *_: {"decision": "keep", "members": [], "reason": "dry run: no model was called"})


class DossierChanged(ValueError):
    pass


def stale_problem(state: Replacements) -> str | None:
    if not state.stale:
        return None
    return (f"dossier_changed: {len(state.stale)} decisions were made on an earlier dossier ({', '.join(sorted(state.stale))}); "
            "rerun with --refresh to ask them again")


def _refreshed(kind: SiteReplaceKind, root: Path, library: PromptLibrary, echo) -> str:
    """A new outbox holding every record but the stale units', so only those are asked again; the old outbox stays.
    Records of another prompt are not carried: that prompt's outbox is not this charter's."""
    kept_charter = charter(library, kept_inputs(root))
    active = active_outbox(root)
    records = active.records() if active.fingerprint == kept_charter.fingerprint else []
    stale = project(kind, records).stale
    if records and not stale:
        echo("refresh: no stale scope; the outbox is kept")
        return kept_charter.inputs
    again = {u.key for u in kind.items() if stale & set(u.unit.members)}
    kept = [r for r in records if r.item not in again]
    inputs = refresh_inputs()
    carry(root, charter(library, inputs), [replace_record(r, seq=n) for n, r in enumerate(kept, 1)])
    echo(f"refresh: {len(stale)} stale scopes asked again, {len(kept)} records kept")
    return inputs


def replace(run_path: Path, app: str, conversations: Conversations, library: PromptLibrary, limits: Limits = Limits(),
            limit: int | None = None, echo=print, refresh: bool = False) -> Replacements:
    """refresh: the scopes whose dossier changed since their decision are asked again; by default they stay, flagged stale."""
    paths = rd.AppPaths(run_path, app)
    kind = SiteReplaceKind(app, read_json(paths.dossiers), paths.root)
    require(str(paths.dossiers), kind.problems)
    inputs = _refreshed(kind, paths.replace, library, echo) if refresh else kept_inputs(paths.replace)
    state = decide(kind, charter(library, inputs), conversations, paths.replace, limits, limit, echo,
                   Where("replace", "site-replace", app))
    counts: dict[str, int] = {}
    for scope, r in state.replacements.items():
        key = f"{r.decision} ({state.sources[scope]})"
        counts[key] = counts.get(key, 0) + 1
    members = sum(len(u.dossiers) for u in kind.items())
    echo(f"{app}: {members + len(kind.no_options)} sites, {len(kind.items())} units asked, {counts}"
         + (f", {len(state.stale)} stale" if state.stale else ""))
    return state
