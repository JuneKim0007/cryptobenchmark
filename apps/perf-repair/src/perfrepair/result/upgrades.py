"""A broken use's upgrade: candidates ranked by their own measured numbers, the edits that apply one, and what makes it a
person's: all from facts code holds, never from a model's risk list."""
from __future__ import annotations

import math
import statistics

from ..dto import PrimitiveRow, Summary
from ..dto.change import MIGRATION, REACH_REVIEW
from ..dto.dossier import Option
from cryptobench.catalogue.grouping import algorithm_of, provider_of
from ..dto.perf_mode import PerfMode
from ..dto.replacement import OUTPUT_LEAVES, Edit, required_risks
from ..dto.site import Scope
from ..dto.upgrade import NEEDS_MIGRATION, UPGRADED, Upgrade, UpgradeItem
from .change import reach
from .configurations import Config, operations

LINKED, KEY_HELD, PARAMETERS_UNKNOWN = "linked_members", "provider_held_key", "parameters_unknown"
# what a set_algorithm or pin_parameters edit cannot carry; a local output's reach alone is not on it
REACH_RETURNED = REACH_REVIEW["return"]
BLOCKS_EDIT = ("reach_persist", "reach_unknown", "field_bound", "key_changes", "parameter_changes", "adds_dependency")


def _at_site(s: Scope, rows: dict[Config, PrimitiveRow]) -> list[PrimitiveRow]:
    """The rows of the site's operations and key size, at the input size nearest its own; each widens when none match."""
    ops = operations(s)
    picked = [c for c in rows if not ops or c.operation in ops] or list(rows)
    picked = [c for c in picked if c.keySize == s.keySize] or picked
    if s.inputSize is not None and picked:
        gap = min(abs((c.inputSize or 0) - s.inputSize) for c in picked)
        picked = [c for c in picked if abs((c.inputSize or 0) - s.inputSize) == gap]
    return [rows[c] for c in picked]


def rank(s: Scope, rows: dict[Config, PrimitiveRow], measurements: dict[str, dict[str, Summary | None]],
         perf: PerfMode) -> tuple[float, ...]:
    """Per selected metric, the candidate's own median at this site, lower first; inf when it has none. Another key size
    than the current's leaves no ratio, so a candidate is never ranked against the current."""
    at_site = _at_site(s, rows)
    found = [[m.median for r in at_site if (m := (measurements.get(r.rowId) or {}).get(name)) is not None]
             for name in perf.names]
    return tuple(statistics.median(values) if values else math.inf for values in found)


def measured_enough(key: tuple[float, ...], perf: PerfMode) -> bool:
    """A number of each required metric, and of one at least: generic requires none."""
    by_name = dict(zip(perf.names, key))
    return any(map(math.isfinite, key)) and all(math.isfinite(by_name[m.name]) for m in perf.required)


def edits_of(current: str, option: Option) -> tuple[Edit, ...]:
    """The edit kinds whose value differs from the current call's, as the replace gate requires them."""
    found = []
    if provider_of(option.item) != provider_of(current):
        found.append(Edit("set_provider", provider=provider_of(option.item)))
    if algorithm_of(option.item) != algorithm_of(current):
        found.append(Edit("set_algorithm", algorithm=algorithm_of(option.item)))
    if option.pins:
        found.append(Edit("pin_parameters", parameters=dict(option.pins)))
    return tuple(found)


def _returned(s: Scope) -> bool:
    """Its callers are not read, so a returned output may be stored; only its own function's comparisons show it stays."""
    return reach(s) == "return" and not (s.lifecycle is not None and s.lifecycle.outputCompared)


def needs_person(item: UpgradeItem, option: Option) -> tuple[str, ...]:
    """Why this upgrade cannot be an automatic edit; stored or sent output comes from the scope's sinks and reach."""
    found = [r for r in required_risks(item.dossier.scope) if r in OUTPUT_LEAVES]
    found += [LINKED] * bool(item.linked) + [KEY_HELD] * item.providerHeld + [PARAMETERS_UNKNOWN] * (option.pins is None)
    found += [REACH_RETURNED] * _returned(item.dossier.scope) + [r for r in option.needsReview if r in BLOCKS_EDIT]
    return tuple(found or ([MIGRATION] if option.change == MIGRATION else ()))


def settled(item: UpgradeItem, option: Option, source: str, reason: str) -> Upgrade:
    needs = needs_person(item, option)
    current = item.dossier.current
    return Upgrade(item.key, current, NEEDS_MIGRATION if needs else UPGRADED, option.item, source, reason,
                   () if needs else edits_of(current, option), needs, option.needsReview)
