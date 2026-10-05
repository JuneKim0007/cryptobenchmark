"""One measured case as the charts and the summary need it: statistics on ns/op, shown in the unit that fits its group."""
import re

import stats
from chart_input import UNIDENTIFIED

PAYLOAD_GROUPS = {1, 4, 5}      # symmetric-cipher, hash, mac: cost scales with the input, so MB/s means something


def runs_of(case):
    metrics = case.get("metrics") or {}
    return (metrics.get("timeNs") or {}).get("runs") or case["nanosPerOperation"]


def size_label(size):
    return "n-a" if size is None else (f"{size}B" if size < 1024 else f"{size // 1024}KiB")


def short(algorithm):
    return re.sub(r"(PKCS5Padding|NoPadding|AndMGF1Padding|/ECB)", "", algorithm).strip("-/")


def summarize_case(case, groups, cfg):
    ns = stats.summarize(runs_of(case))
    group_id, group_label = groups.get(case["id"], UNIDENTIFIED)
    size = case.get("inputSize")
    if group_id in PAYLOAD_GROUPS and size:       # monotone, so the quartiles swap ends; the mean is the throughput of the mean time
        f = lambda t: size / t * 1000
        shown = dict(mean=f(ns["mean"]), median=f(ns["median"]), q1=f(ns["q3"]), q3=f(ns["q1"]), min=f(ns["max"]), max=f(ns["min"]))
        unit = "MB/s"
    else:
        f = lambda t: t / 1000
        shown = dict(mean=f(ns["mean"]), median=f(ns["median"]), q1=f(ns["q1"]), q3=f(ns["q3"]), min=f(ns["min"]), max=f(ns["max"]))
        unit = "us/op"
    return {
        "id": case["id"], "group": group_id, "groupLabel": group_label, "type": case["type"], "algorithm": case["algorithm"],
        "provider": case["provider"], "operation": case["operation"], "keySize": case.get("keySize"), "inputSize": size,
        "unit": unit, "ns": ns, "shown": shown, "lead": stats.headline(ns, cfg["headline"], cfg["limit"]),
        "noisy": ns["cov"] * 100 > cfg["limit"],
    }


TIME = "timeNs"
COUNT_LABELS = {"allocationCount": "allocations per call"}      # any other non-time metric (a CPU event) is labelled by its own name


def count_metrics(raw_cases):
    """The metrics a run carries besides timeNs, in the order first seen; only those with at least one run."""
    names = []
    for case in raw_cases:
        for name, block in (case.get("metrics") or {}).items():
            if name != TIME and (block or {}).get("runs") and name not in names:
                names.append(name)
    return names


def summarize_count(case, groups, metric):
    """One case's runs of a count metric, as measured: no unit conversion. None when the case has no runs for it."""
    runs = ((case.get("metrics") or {}).get(metric) or {}).get("runs") or []
    if not runs:
        return None
    group_id, group_label = groups.get(case["id"], UNIDENTIFIED)
    return {
        "id": case["id"], "group": group_id, "groupLabel": group_label, "type": case["type"], "algorithm": case["algorithm"],
        "provider": case["provider"], "operation": case["operation"], "keySize": case.get("keySize"), "inputSize": case.get("inputSize"),
        "metric": metric, "label": COUNT_LABELS.get(metric, metric), "runs": list(runs), "stats": stats.summarize(runs),
    }
