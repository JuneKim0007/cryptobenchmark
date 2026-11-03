"""The truth check of a scope's category: the selected metrics whose before/after change, beyond noise, is not a
change its category's estimates gave."""
from __future__ import annotations

from .gain import UNCHANGED, change_of


def category_mismatch(metrics: list[dict], estimates: list[dict]) -> list[str]:
    """A function doing more than the primitive dilutes the ratio toward 1, so a measured `unchanged` never counts."""
    out = []
    for m in metrics:
        if not (m["measured"] and m["selected"]) or m["change"] == UNCHANGED:
            continue
        estimated = {change_of(e["ratio"], e["pImprove"]) for e in estimates if e["metric"] == m["metric"]}
        if estimated and m["change"] not in estimated:
            out.append(m["metric"])
    return out
