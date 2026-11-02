"""summarize(): one run's events per stage and per app folder: time, items, model calls, rejections, tokens, cost."""
from __future__ import annotations

import re
from collections import Counter
from datetime import datetime

from ..dto.event import DECISION, END, LOG, RUN_END, RUN_START, TURN, Event

TOP = 5
_TURN_PREFIX = re.compile(r"^s\d+t\d+: ")


def _ts(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def runs(events: list[Event]) -> list[str]:
    return list(dict.fromkeys(e.run for e in events))


def _span_ms(events: list[Event]) -> int:
    return int((_ts(events[-1].ts) - _ts(events[0].ts)).total_seconds() * 1000)


def _add_tokens(total: dict, tokens: dict | None) -> None:
    for k, v in (tokens or {}).items():
        total[k] = total.get(k, 0) + int(v or 0)


def block(events: list[Event]) -> dict:
    """The numbers of one group of events; a turn is one model call."""
    turns = [e for e in events if e.event == TURN]
    decisions = [e for e in events if e.event == DECISION]
    problems = Counter(_TURN_PREFIX.sub("", p) for e in turns for p in e.data.get("problems") or ())
    tokens: dict = {}
    for e in turns:
        _add_tokens(tokens, e.tokens)
    costs = [e.costUsd for e in turns if e.costUsd is not None]
    steps: dict[str, dict] = {}
    for e in events:
        if e.event == END and e.kind == "static":
            s = steps.setdefault(e.step, {"runs": 0, "durationMs": 0, "outcomes": {}})
            s["runs"] += 1
            s["durationMs"] += e.durationMs or 0
            s["outcomes"][e.outcome] = s["outcomes"].get(e.outcome, 0) + 1
    slowest = sorted(decisions, key=lambda e: -(e.durationMs or 0))[:TOP]
    return {"durationMs": _span_ms(events), "steps": steps,
            "items": len({(e.step, e.item) for e in decisions}),
            "decisions": dict(Counter(e.outcome for e in decisions)),
            "modelCalls": len(turns), "rejections": sum(e.outcome != "accepted" for e in turns),
            "topProblems": [{"problem": p, "count": n} for p, n in problems.most_common(TOP)],
            "slowest": [{"step": e.step, "item": e.data.get("label") or e.item, "durationMs": e.durationMs,
                         "turns": e.data.get("turns")} for e in slowest],
            "tokens": tokens or None, "costUsd": round(sum(costs), 6) if costs else None}


def summarize(events: list[Event], run: str | None = None) -> dict:
    """run: a run id; None is the last run in the file."""
    ids = runs(events)
    if not ids:
        raise ValueError("no_events: events.jsonl holds no run")
    chosen = run or ids[-1]
    if chosen not in ids:
        raise ValueError(f"run_unknown: {chosen}; events.jsonl holds {', '.join(ids)}")
    of_run = [e for e in events if e.run == chosen]
    # plain log records (settings, warnings) belong to no stage's numbers
    mine = [e for e in of_run if e.stage != "run" and e.event != LOG]
    end = next((e for e in of_run if e.event == RUN_END), None)
    start = next((e for e in of_run if e.event == RUN_START), None)
    by_stage: dict[str, list[Event]] = {}
    by_app: dict[str, list[Event]] = {}
    for e in mine:
        by_stage.setdefault(e.stage, []).append(e)
        if e.app:
            by_app.setdefault(e.app, []).append(e)
    return {"run": chosen, "command": start.detail if start else None,
            "outcome": end.outcome if end else "running", "durationMs": end.durationMs if end else _span_ms(of_run),
            "total": block(of_run), "stages": {s: block(es) for s, es in by_stage.items()},
            "apps": {a: block(es) for a, es in by_app.items()}}
