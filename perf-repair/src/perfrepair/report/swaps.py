"""The report rows of every app → one view per chosen swap (current → option): each metric's gain or loss across the apps
that use it, and how many of its scopes carry each label."""
from __future__ import annotations

import statistics
from collections import defaultdict

from ..result.gain import L_NOT_MEASURED, L_TRADE_OFF, LABELS, change_of


def _row_metrics(rows: list[tuple[str, dict]]) -> dict:
    metrics: dict[str, dict] = defaultdict(lambda: defaultdict(list))
    for app, s in rows:
        for m in s["metrics"]:
            if m["measured"] and m["ratio"] is not None:
                metrics[m["metric"]][app].append((m["ratio"], m["pImprove"]))
    return {name: _metric(apps) for name, apps in metrics.items()}


def _metric(apps: dict) -> dict:
    ratios = {app: statistics.median(r for r, _ in pairs) for app, pairs in sorted(apps.items())}
    every = [pair for pairs in apps.values() for pair in pairs]
    changes = [change_of(r, p) for r, p in every]
    return {"ratios": ratios, "medianRatio": statistics.median(ratios.values()), "scopes": len(every),
            "changes": {c: changes.count(c) for c in sorted(set(changes))}}


def swaps(reports: list[dict]) -> list[dict]:
    """Every replace decision's pair, in name order; a swap nothing measured still lists its scopes."""
    chosen: dict[tuple[str, str], list[tuple[str, dict]]] = defaultdict(list)
    for r in reports:
        for s in r["scopes"]:
            if s["decision"]["decision"] == "replace" and s["current"] and s["option"]:
                chosen[(s["current"], s["option"])].append((r["app"], s))
    return [{"current": current, "option": option, "apps": sorted({app for app, _ in rows}),
             "labels": {k: sum(s["label"] == k for _, s in rows) for k in LABELS if any(s["label"] == k for _, s in rows)},
             "metrics": _row_metrics(rows)}
            for (current, option), rows in sorted(chosen.items())]


def label_counts(reports: list[dict]) -> dict:
    """The replace decisions by the label their measurement earned: a trade-off shipped is one the decision accepted."""
    rows = [s for r in reports for s in r["scopes"] if s["decision"]["decision"] == "replace"]
    found = {k: sum(s["label"] == k for s in rows) for k in LABELS}
    return {"improves": found["improves"], "tradeOffAccepted": found[L_TRADE_OFF], "worse": found["worse"],
            "unchanged": found["unchanged"], "notMeasured": found[L_NOT_MEASURED]}
