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
