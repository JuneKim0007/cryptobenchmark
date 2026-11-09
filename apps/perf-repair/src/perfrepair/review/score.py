"""The sheet's verdicts and the attempt logs' turns → grouping precision, pick accuracy, gate rejections per 100 calls."""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from cryptobench.paths import RunTree
from cryptobench.paths import AI_LOGS
from ..ai.log.attempt_log import read_log
from ..files import write_json
from .sheet import GROUPING, read_sheet
from ..stop.halt import Coded

OK, WRONG = "ok", "wrong"
# turns that answered nothing the gate took: a rejection or a refusal
REJECTED = ("rejected", "refused")


def _share(right: int, judged: int) -> dict:
    """value None: nothing judged yet, which is not a score of zero."""
    return {"value": right / judged if judged else None, "right": right, "judged": judged}


def _verdicts(sheet: list[dict]) -> list[dict]:
    bad = sorted({r["verdict"] for r in sheet} - {"", OK, WRONG})
    if bad:
        raise Coded(f"review_verdict: {bad} in the sheet; a verdict is {OK}, {WRONG} or empty")
    return [r for r in sheet if r["verdict"]]


def _judged(rows: list[dict]) -> dict:
    return _share(sum(r["verdict"] == OK for r in rows), len(rows))


def _rejections(calls: dict[str, int], rejected: dict[str, int]) -> dict:
    per = {k: {"calls": calls[k], "rejected": rejected[k], "per100": 100 * rejected[k] / calls[k]} for k in sorted(calls)}
    total, bad = sum(calls.values()), sum(rejected.values())
    return {"calls": total, "rejected": bad, "per100": 100 * bad / total if total else None, "byKind": per}


def score(device: Path) -> dict:
    device = Path(device)
    judged = _verdicts(read_sheet(RunTree(device).review.decisions))
    calls, rejected = defaultdict(int), defaultdict(int)
    for path in sorted((device / AI_LOGS).glob("*.yaml")):
        doc = read_log(path)
        for turn in (t for a in doc["attempts"] for t in a.get("turns") or ()):
            calls[doc["job"]] += 1
            rejected[doc["job"]] += turn["status"] in REJECTED
    doc = {"decisions": len(read_sheet(RunTree(device).review.decisions)),
           "groupingPrecision": _judged([r for r in judged if r["kind"] == GROUPING]),
           "pickAccuracy": _judged([r for r in judged if r["kind"] != GROUPING]),
           "gateRejections": _rejections(calls, rejected)}
    write_json(RunTree(device).review.score, doc)
    return doc
