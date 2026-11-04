"""check_dossier: one dossier on its own; the run check and the replace stage share it."""
from __future__ import annotations

import math

from ...dto.change import (
    DROP_IN,
    NEEDS_REVIEW,
    PROVIDER_PATH,
    REACHES,
    TRACKS,
    admits,
    output_changes,
)
from ...dto.dossier import NO_ESTIMATE_REASONS, NO_REAL_USE, OPTION_PREFIX, Dossier
from ...dto.grouping import parse_qualified, provider_of
from ...dto.interop import PAIR_STATUSES
from ...dto.lifecycle import NO_REAL_USE as NO_REAL_USE_STATUS
from ...dto.perf_mode import PerfMode
from ...dto.screen import STATUSES
from ...result.estimate import MIN_RUNS
from ...result.gain import no_gain
from ..app import scope_problems


def raw_scope_id(raw) -> str | None:
    scope = raw.get("scope") if isinstance(raw, dict) else None
    return scope.get("id") if isinstance(scope, dict) else None


def _qualified(item) -> bool:
    try:
        parse_qualified(item)
    except (ValueError, AttributeError):
        return False
    return True


def _number(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def _changes(where: str, d: Dossier, max_change: str) -> list[str]:
    """Each option within maxChange; a drop-in carries no diff, any other class carries one."""
    problems = [f"{where} {o.alias}: change {o.change!r} is above maxChange {max_change}" for o in d.options
                if not admits(max_change, o.change)]
    return problems + [f"{where} {o.alias}: {o.change} {'with' if o.diff else 'without'} a pair diff" for o in d.options
                       if (o.diff is None) != (o.change == DROP_IN)]


def _review(where: str, d: Dossier) -> list[str]:
    """outputChanges, reach and needsReview are what code computed from the diff and the scope, never a judgement."""
    problems = [f"{where} {o.alias}: reach {o.reach!r} is not one of {REACHES}" for o in d.options if o.reach not in REACHES]
    problems += [f"{where} {o.alias}: outputChanges {o.outputChanges!r} does not follow its pair diff" for o in d.options
                 if o.outputChanges is not output_changes(o.diff)]
    problems += [f"{where} {o.alias}: track {o.track!r} is not one of {TRACKS}" for o in d.options if o.track not in TRACKS]
    problems += [f"{where} {o.alias}: a provider_path is a drop-in from another provider" for o in d.options
                 if o.track == PROVIDER_PATH and (o.change != DROP_IN or provider_of(o.item) == provider_of(d.current))]
    return problems + [f"{where} {o.alias}: needsReview {list(o.needsReview)} is not a list of {NEEDS_REVIEW}"
                       for o in d.options if not set(o.needsReview) <= set(NEEDS_REVIEW)]


def _gained(where: str, d: Dossier) -> list[str]:
    return [f"{where} {o.alias}: one metric proven worse and none better; such a candidate is rejected no_gain"
            for o in d.options if no_gain(o.estimates)]


def _estimates(where: str, d: Dossier, selected: tuple[str, ...]) -> list[str]:
    problems = []
    for o in d.options:
        for e in o.estimates:
            at = f"{where} {o.alias} {e.metric}"
            if e.metric not in selected:
                problems.append(f"{at}: metric is not one of the perfMode's {selected}")
            if not (_number(e.ratio) and e.ratio > 0):
                problems.append(f"{at}: ratio {e.ratio!r} is not a positive number")
            p, n = e.pImprove, e.n
            if not isinstance(n, int) or n < MIN_RUNS:
                problems.append(f"{at}: n {n!r}; an estimate needs {MIN_RUNS} runs a side")
            elif p is None:
                problems.append(f"{at}: pImprove is empty with n {n}")
            if p is not None and not (_number(p) and 0 <= p <= 1):
                problems.append(f"{at}: pImprove {p!r} is not a probability")
    return problems + _no_estimates(where, d, selected)


def _no_estimates(where: str, d: Dossier, selected: tuple[str, ...]) -> list[str]:
    return [f"{where} {o.alias} {n.metric}: no-estimate reason {n.reason!r} is not one of {NO_ESTIMATE_REASONS}, or the "
            f"metric is not selected" for o in d.options for n in o.noEstimates
            if n.reason not in NO_ESTIMATE_REASONS or n.metric not in selected]


def check_dossier(raw, app: str | None, perf: PerfMode, max_change: str = DROP_IN) -> tuple[Dossier | None, list[str]]:
    """One dossier on its own: its scope, its items, its aliases R1..Rn, its pins, interop labels, estimates of
    perf's metrics only and change classes within max_change."""
    where = f"dossier {raw_scope_id(raw)}"
    if not isinstance(raw, dict):
        return None, [f"{where}: is not an object"]
    problems = scope_problems(where, raw.get("scope"), app)
    if problems:
        return None, problems
    try:
        d = Dossier.from_json(raw)
    except (KeyError, TypeError, ValueError, AttributeError) as e:
        return None, [f"{where}: does not parse into Dossier: {e!r}"]
    if not isinstance(d.source, str) or not d.source.strip():
        problems.append(f"{where}: source is empty")
    items = [d.current] + [o.item for o in d.options]
    problems += [f"{where}: {item!r} is not a qualified item id" for item in items if not _qualified(item)]
    if not d.options:
        problems.append(f"{where}: no options; such a scope belongs in noOptions")
    if d.scope.lifecycle is not None and d.scope.lifecycle.status == NO_REAL_USE_STATUS:
        problems.append(f"{where}: lifecycle {NO_REAL_USE_STATUS}; such a scope belongs in noOptions as {NO_REAL_USE}")
    if [o.alias for o in d.options] != [f"{OPTION_PREFIX}{n}" for n in range(1, len(d.options) + 1)]:
        problems.append(f"{where}: aliases are not R1..R{len(d.options)} in order")
    if len(set(items)) != len(items):
        problems.append(f"{where}: an option repeats the current item or another option")
    problems += [f"{where} {o.alias}: screen {o.screen!r} is neither one of {STATUSES} nor null"
                 for o in d.options if o.screen is not None and o.screen not in STATUSES]
    return d, problems + _labels(where, d) + _estimates(where, d, perf.names) + _changes(where, d, max_change) + _gained(where, d) + _review(where, d)


def _labels(where: str, d: Dossier) -> list[str]:
    problems = [f"{where} {o.alias}: pins {o.pins!r} is neither an object nor null (unknown)"
                for o in d.options if o.pins is not None and not isinstance(o.pins, dict)]
    problems += [f"{where} {o.alias}: interop {o.interop!r} is not one of {PAIR_STATUSES}"
                 for o in d.options if o.interop not in PAIR_STATUSES]
    problems += [f"{where} {o.alias}: interop fail; a failed pair is never an option"
                 for o in d.options if o.interop == "fail"]
    return problems
