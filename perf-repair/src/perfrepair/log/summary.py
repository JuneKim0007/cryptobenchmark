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


def _steps(events: list[Event]) -> dict[str, dict]:
    steps: dict[str, dict] = {}
    for e in (e for e in events if e.event == END and e.kind == "static"):
        s = steps.setdefault(e.step, {"runs": 0, "durationMs": 0, "outcomes": {}})
        s["runs"] += 1
        s["durationMs"] += e.durationMs or 0
        s["outcomes"][e.outcome] = s["outcomes"].get(e.outcome, 0) + 1
    return steps


def _usage(turns: list[Event]) -> dict:
    tokens: dict = {}
    for e in turns:
        for k, v in (e.tokens or {}).items():
            tokens[k] = tokens.get(k, 0) + int(v or 0)
    costs = [e.costUsd for e in turns if e.costUsd is not None]
    return {"tokens": tokens or None, "costUsd": round(sum(costs), 6) if costs else None}


def _slowest(decisions: list[Event]) -> list[dict]:
    return [{"step": e.step, "item": e.data.get("label") or e.item, "durationMs": e.durationMs,
             "turns": e.data.get("turns")} for e in sorted(decisions, key=lambda e: -(e.durationMs or 0))[:TOP]]


def _problems(turns: list[Event]) -> list[dict]:
    problems = Counter(_TURN_PREFIX.sub("", p) for e in turns for p in e.data.get("problems") or ())
    return [{"problem": p, "count": n} for p, n in problems.most_common(TOP)]


def _of(events: list[Event], name: str) -> list[Event]:
    return [e for e in events if e.event == name]


def block(events: list[Event]) -> dict:
    """The numbers of one group of events; a turn is one model call."""
    turns, decisions = _of(events, TURN), _of(events, DECISION)
    return {"durationMs": _span_ms(events), "steps": _steps(events),
            "items": len({(e.step, e.item) for e in decisions}),
            "decisions": dict(Counter(e.outcome for e in decisions)),
            "modelCalls": len(turns), "rejections": sum(e.outcome != "accepted" for e in turns),
            "topProblems": _problems(turns),
            "slowest": _slowest(decisions), **_usage(turns)}


def _grouped(events: list[Event], key) -> dict[str, dict]:
    groups: dict[str, list[Event]] = {}
    for e in events:
        if key(e):
            groups.setdefault(key(e), []).append(e)
    return {name: block(es) for name, es in groups.items()}


def _chosen(events: list[Event], run: str | None) -> str:
    ids = runs(events)
    if not ids:
        raise ValueError("no_events: events.jsonl holds no run")
    if run is not None and run not in ids:
        raise ValueError(f"run_unknown: {run}; events.jsonl holds {', '.join(ids)}")
    return run or ids[-1]


def summarize(events: list[Event], run: str | None = None) -> dict:
    """run: a run id; None is the last run in the file."""
    chosen = _chosen(events, run)
    of_run = [e for e in events if e.run == chosen]
    # plain log records (settings, warnings) belong to no stage's numbers
    staged = [e for e in of_run if e.stage != "run" and e.event != LOG]
    return {"run": chosen, **_bounds(of_run), "total": block(of_run), "stages": _grouped(staged, lambda e: e.stage),
            "apps": _grouped(staged, lambda e: e.app)}


def _bounds(of_run: list[Event]) -> dict:
    """The command, and how the run ended; one still writing is `running`, its time so far."""
    starts, ends = _of(of_run, RUN_START), _of(of_run, RUN_END)
    command = starts[0].detail if starts else None
    if not ends:
        return {"command": command, "outcome": "running", "durationMs": _span_ms(of_run)}
    return {"command": command, "outcome": ends[0].outcome, "durationMs": ends[0].durationMs}
