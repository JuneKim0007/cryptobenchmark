"""A report row's metric rows: an unmeasured one with its reason, a measured one's numbers by the rule, the time row's views."""
from __future__ import annotations

import math

from ..dto.metrics import BY_NAME
from ..dto.report import has_views
from ..dto.units import DisplayUnits
from ..result.confidence import level
from ..result.gain import change_of, noise_of

MEASURED_KEYS = {"metric", "unit", "selected", "measured", "before", "after", "ratio", "pImprove", "level", "n", "noise", "change"}


def _views(where: str, m: dict, units: DisplayUnits) -> list[str]:
    """The time row's display: latency is its medians in the latency unit, throughput their inverse in its unit or null."""
    v = m.get("views")
    if "views" not in m:
        return []
    if v is None:
        return [] if not (m["before"] > 0 and m["after"] > 0) else [f"{where}: views null for positive medians"]
    lat, tput = v.get("latency") or {}, v.get("throughput")
    if lat != {"unit": units.latency_label, "before": units.latency_of(m["before"]), "after": units.latency_of(m["after"])}:
        return [f"{where}: latency view {lat} is not the medians in {units.latency_label}"]
    if tput is not None and (tput.get("unit") != units.throughput
                             or not math.isclose(tput["before"] * m["before"], tput["after"] * m["after"], rel_tol=1e-9)):
        return [f"{where}: throughput view {tput} is not the medians' inverse in {units.throughput}"]
    return []


def _extra(m: dict) -> set[str]:
    """The keys a measured row adds: views on the time metric, else kind when energy was estimated."""
    metric = BY_NAME.get(m.get("metric"))
    return {"views"} if metric and has_views(metric) else set(m) & {"kind"}


def check_selected(where: str, metrics: list[dict], selected: tuple[str, ...]) -> list[str]:
    return [f"{where}.{m.get('metric')}: selected {m.get('selected')!r} is not whether the mode selects it"
            for m in metrics if m.get("selected") is not (m.get("metric") in selected)]


def check_metric(where: str, m: dict, units: DisplayUnits) -> list[str]:
    if m.get("measured") is False:
        ok = set(m) == {"metric", "unit", "selected", "measured", "reason"} and isinstance(m["reason"], str) and m["reason"]
        return [] if ok else [f"{where}: an unmeasured metric has exactly a non-empty reason and no numbers"]
    if set(m) != MEASURED_KEYS | _extra(m):
        return [f"{where}: keys {sorted(m)}"]
    problems = []
    if not all(isinstance(m[k], (int, float)) and math.isfinite(m[k]) and m[k] >= 0 for k in ("before", "after")):
        problems.append(f"{where}: before and after must be finite and not negative")
    elif m["ratio"] != (m["after"] / m["before"] if m["before"] else None):
        problems.append(f"{where}: ratio {m['ratio']} is not after ÷ before")
    if m["level"] != level(m["pImprove"]):
        problems.append(f"{where}: level {m['level']} is not the grade of pImprove {m['pImprove']}")
    if m["noise"] != noise_of(m["pImprove"]) or m["change"] != change_of(m["ratio"], m["pImprove"]):
        problems.append(f"{where}: noise {m['noise']} or change {m['change']} is not the rule's for its ratio and pImprove")
    return problems or _views(where, m, units)
