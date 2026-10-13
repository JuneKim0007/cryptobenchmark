"""TEMP: before/after for one call site from a benchmark run of its item and its replacement, not the whole app."""
from __future__ import annotations

import statistics


def _case(cases: list[dict], engine_type: str, name: str, provider: str, input_size: int | None) -> dict:
    for c in cases:
        if (c["type"], c["algorithm"], c["provider"], c.get("inputSize")) == (engine_type, name, provider, input_size):
            return c
    raise KeyError(f"{engine_type} {name} {provider} input {input_size}: not in the benchmark")


def side(benchmark: dict, energy: dict | None, engine_type: str, name: str, provider: str, input_size: int | None) -> dict:
    c = _case(benchmark["cases"], engine_type, name, provider, input_size)
    runs = c["metrics"]["timeNs"]["runs"]
    mean = statistics.fmean(runs)
    window = ((energy or {}).get("cases") or {}).get(c["id"]) or {}
    joules = window.get("joulesPerOperation") if window.get("valid") else None
    return {"case": c["id"], "meanNs": mean, "medianNs": statistics.median(runs), "runs": len(runs),
            "mbPerSecond": input_size / mean * 1e3 if input_size else None,
            "microjoulesPerOp": joules * 1e6 if joules is not None else None}


def compare(before: dict, after: dict) -> dict:
    return {"before": before, "after": after, "speedup": before["meanNs"] / after["meanNs"],
            "energyRatio": (after["microjoulesPerOp"] / before["microjoulesPerOp"]
                            if before["microjoulesPerOp"] and after["microjoulesPerOp"] else None)}
