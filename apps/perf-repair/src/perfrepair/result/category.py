"""The truth check of a scope's category: the selected metrics whose before/after change, beyond noise, is not a
change its category's estimates gave."""
from __future__ import annotations

from ..dto.pattern import FIXED
from ..dto.report import FUNCTION
from .configurations import parse_label
from .gain import UNCHANGED, change_of


def category_mismatch(metrics: list[dict], estimates: list[dict], diluted: bool = True) -> list[str]:
    """A function doing more than the primitive dilutes the ratio toward 1, so its measured `unchanged` never counts; the call alone is not diluted."""
    out = []
    for m in metrics:
        if not (m["measured"] and m["selected"]) or (diluted and m["change"] == UNCHANGED):
            continue
        estimated = {change_of(e["ratio"], e["pImprove"]) for e in estimates if e["metric"] == m["metric"]}
        if estimated and m["change"] not in estimated:
            out.append(m["metric"])
    return out


def at_call_site(estimates: list[dict], operation: str | None, inputs: dict | None) -> list[dict]:
    """The estimates at the call's own operation and sizes, else at its operation, else every one the option has."""
    labelled = [(e, parse_label(e["configuration"])) for e in estimates]
    same = [(e, m) for e, m in labelled if m and m["op"] == operation]
    sizes = inputs or {}
    exact = [e for e, m in same if m["key"] == str(sizes.get("keySize")) and m["input"] == str(sizes.get("inputSize"))]
    return exact or [e for e, _ in same] or estimates


def truth(kind: str, pattern: str, metrics: list[dict], estimates: list[dict]) -> dict:
    """One kind of number against the dossier's estimates of the scope's category; the verdict and what it compared."""
    base = {"category": pattern, "mismatch": [], "compared": []}
    if kind == FUNCTION and pattern == FIXED:
        return {"verdict": "not_applicable", **base}
    compared = []
    for m in metrics:
        if m["measured"] and m["selected"]:
            found = [e for e in estimates if e["metric"] == m["metric"]]
            compared.append({"metric": m["metric"], "ratio": m["ratio"], "change": m["change"], "estimatedRatios": [e["ratio"] for e in found],
                             "estimatedChanges": sorted({change_of(e["ratio"], e["pImprove"]) for e in found})})
    mismatch = category_mismatch(metrics, estimates, diluted=kind == FUNCTION)
    verdict = ("not_measured" if not compared else "no_estimate" if not any(c["estimatedRatios"] for c in compared)
               else "contradicts" if mismatch else "agrees")
    return {"verdict": verdict, **base, "mismatch": mismatch, "compared": compared}


def checkable(scope: dict) -> bool:
    """A fixed scope's function is its setup, so its before/after is not the per-call path the category estimates."""
    return scope.get("pattern") != "fixed"
