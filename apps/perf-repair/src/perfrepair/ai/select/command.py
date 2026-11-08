"""Stage: an app's broken uses and units through Select, one settings row (apps.replace), one log (log/ai/select.yaml);
upgrades.json and replacements.json."""
from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from ...dto.prompt import TaskPrompt
from ...inputs.table import APPS_REPLACE
from ..attempt.escalate import next_tier
from ..log.attempt_log import AttemptLog
from ..log.where import Where
from ..runtime.agent import ScriptedConversations
from ..review.job import NAME as REVIEW, ReviewJob
from ..runtime.engine.ask import Limits
from ..runtime.gateway.spawn import Spawned, spawned_of
from ..runtime.prompt import PromptLibrary
from ..tools.registry import Registry
from .candidate import NONE
from .job import NAME, SelectJob
from .replacements import Replacements
from .units import UnitSource
from .upgrade_state import UpgradeState
from .upgrades import UpgradeSource

ROLE = APPS_REPLACE
FIRST_ALIAS = re.compile(r"^  ([A-Z]\d+) = ", re.M)


def _dry_run(task: TaskPrompt, *_):
    """none where it is allowed, else the first candidate; a reviewer's question is accepted."""
    if task.name != NAME:
        return {"tool": "verdict", "args": {"verdict": "accept", "reason": "dry run: no model was called"}}
    first = FIRST_ALIAS.search(task.text)
    pick = NONE if "or none" in task.text or first is None else first.group(1)
    return {"tool": "submit", "args": {"option": pick, "reason": "dry run: no model was called"}}


def dry_run() -> ScriptedConversations:
    """The dry-run gateway's stand-in, one per command, so what it records lasts only as long as the command."""
    return ScriptedConversations(_dry_run)


def _run(source, run_path: Path, app: str, spawned: Spawned, library: PromptLibrary, limits: Limits, limit: int | None, echo,
         review: bool):
    where, registry = Where("replace", NAME, app), Registry()
    reviewer = None
    if review:
        # the reviewer asks one tier up the ladder, or the same tier when there is none
        spawned = spawned_of(spawned)
        above = spawned.at(next_tier(spawned.tier, spawned.ladder) or spawned.tier)
        reviewer = ReviewJob(above, library, AttemptLog(run_path, REVIEW, where, echo), registry, limits)
    SelectJob(spawned, library, AttemptLog(run_path, NAME, where, echo), registry, source, limits, reviewer).run(limit)
    return source.state


def select_upgrades(run_path: Path, app: str, spawned: Spawned, library: PromptLibrary, limits: Limits = Limits(),
                    limit: int | None = None, echo=print, review: bool = False) -> UpgradeState:
    return _run(UpgradeSource(run_path, app), run_path, app, spawned, library, limits, limit, echo, review)


def select_units(run_path: Path, app: str, spawned: Spawned, library: PromptLibrary, limits: Limits = Limits(),
                 limit: int | None = None, echo=print, review: bool = False) -> Replacements:
    """review: a reviewer one tier up reads each answer; a refusal is the next repass's reason."""
    source = UnitSource(run_path, app)
    state = _run(source, run_path, app, spawned, library, limits, limit, echo, review)
    counts = Counter(f"{r.decision} ({state.sources[k]})" for k, r in state.replacements.items())
    echo(f"{app}: {sum(len(u.dossiers) for u in source.units) + len(source.no_options)} sites, {len(source.units)} units, {dict(counts)}")
    return state


def upgrade_counts(state: UpgradeState) -> str:
    """One line of what the broken uses became."""
    found = Counter(u.status for u in state.rows.values())
    return f"{len(state.rows)} broken uses" + "".join(f", {n} {status}" for status, n in sorted(found.items()))
