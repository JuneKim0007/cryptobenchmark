"""The summary as text lines: the runs, then the total, each stage and each app folder, last the status lines."""
from __future__ import annotations

from .views import seconds, tokens_text


def _numbers(b: dict) -> str:
    parts = [seconds(b["durationMs"])]
    if b["modelCalls"]:
        decided = ", ".join(f"{k} {v}" for k, v in sorted(b["decisions"].items()))
        parts += [f"{b['items']} items ({decided})", f"{b['modelCalls']} model calls", f"{b['rejections']} rejected"]
    if b["tokens"]:
        parts.append(tokens_text(b["tokens"]))
    if b["costUsd"] is not None:
        parts.append(f"${b['costUsd']:.4f}")
    return ", ".join(parts)


def _block(title: str, b: dict) -> list[str]:
    lines = [f"{title}: {_numbers(b)}"]
    for step, s in b["steps"].items():
        outcomes = ", ".join(f"{k} {v}" for k, v in s["outcomes"].items())
        lines.append(f"  {step}: {s['runs']}x {seconds(s['durationMs'])} ({outcomes})")
    lines += [f"  problem x{p['count']}: {p['problem']}" for p in b["topProblems"]]
    lines += [f"  slow: {s['step']} {s['item']} {seconds(s['durationMs'])}, {s['turns']} turns"
              for s in b["slowest"] if s["durationMs"]]
    return lines


def _run(r: dict) -> str:
    return f"run {r['run']}: {r['command']}: {r['outcome']} ({seconds(r['durationMs'])})"


def summary_lines(doc: dict) -> list[str]:
    lines = [_run(r) for r in doc["runs"]]
    lines.append(_block(f"total of {len(doc['runs'])} runs" if len(doc["runs"]) > 1 else "total", doc["total"])[0])
    for stage, b in doc["stages"].items():
        lines += _block(f"stage {stage}", b)
    for app, b in doc["apps"].items():
        lines += _block(f"app {app}", b)
    # last, so the lines a person acts on end the output
    return lines + ["status:", *(f"  {line}" for line in doc["status"])] if doc["status"] else lines
