"""The sheet's verdicts and the journals' turns → grouping precision, pick accuracy, stability, gate rejections per 100 calls."""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from .. import run_dir as rd
from ..ai.runtime.engine import journal
from ..files import write_json
from .sheet import GROUPING, choice, read_sheet, stages
from ..stop.halt import Coded

OK, WRONG = "ok", "wrong"
ACCEPTED = "accepted"


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


def _asked_choice(turn: dict) -> str:
    text = (turn.get("reply") or {}).get("text") or ""
    try:
        parsed = json.loads(text)
    except ValueError:
        return text
    return choice(parsed) if isinstance(parsed, dict) else text


def _stability(asks: dict[tuple, list[str]]) -> dict:
    """Items asked twice or more on one message: stable when every accepted answer picks the same."""
    repeated = [picks for picks in asks.values() if len(picks) > 1]
    return {**_share(sum(len(set(p)) == 1 for p in repeated), len(repeated)), "asks": sum(map(len, repeated))}


def _rejections(calls: dict[str, int], rejected: dict[str, int]) -> dict:
    per = {k: {"calls": calls[k], "rejected": rejected[k], "per100": 100 * rejected[k] / calls[k]} for k in sorted(calls)}
    total, bad = sum(calls.values()), sum(rejected.values())
    return {"calls": total, "rejected": bad, "per100": 100 * bad / total if total else None, "byKind": per}


def score(device: Path) -> dict:
    device = Path(device)
    judged = _verdicts(read_sheet(rd.review_sheet(device)))
    calls, rejected, asks = defaultdict(int), defaultdict(int), defaultdict(list)
    for stage in stages(device):
        for turn in journal.read(stage.root / rd.JOURNAL):
            calls[stage.kind] += 1
            if turn["status"] != ACCEPTED:
                rejected[stage.kind] += 1
                continue
            asks[(stage.kind, stage.app, turn["item"], turn.get("messageSha"))].append(_asked_choice(turn))
    doc = {"decisions": len(read_sheet(rd.review_sheet(device))),
           "groupingPrecision": _judged([r for r in judged if r["kind"] == GROUPING]),
           "pickAccuracy": _judged([r for r in judged if r["kind"] != GROUPING]),
           "stability": _stability(asks), "gateRejections": _rejections(calls, rejected)}
    write_json(rd.review_score(device), doc)
    return doc
