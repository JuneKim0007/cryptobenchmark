"""The summary as text lines: the run, then each stage and each app folder."""
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


def summary_lines(doc: dict) -> list[str]:
    lines = [f"run {doc['run']}: {doc['command']}: {doc['outcome']} ({seconds(doc['durationMs'])})",
             *_block("total", doc["total"])[:1]]
    for stage, b in doc["stages"].items():
        lines += _block(f"stage {stage}", b)
    for app, b in doc["apps"].items():
        lines += _block(f"app {app}", b)
    return lines
