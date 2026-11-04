"""report.json and summary.json rendered as Markdown; numbers come only from the document."""
from __future__ import annotations

from ..dto.measurement import ESTIMATED
from ..dto.pattern import PATTERNS, rule_words
from ..dto.report import (
    CALL_SITE,
    CHANGES,
    FUNCTION,
    FUNNEL,
    THERMAL_MISMATCH,
    THERMAL_THROTTLED,
)
from ..dto.units import number

NOT_MEASURED = "not measured"
# marks a metric the perfMode selected: the one a decision saw and the verdict judged
SELECTED = " *"


def _p(m: dict) -> str:
    return "n/a (n<2)" if m["pImprove"] is None else f"{m['pImprove']:.2f} ({m['level']})"


def _step(s: dict) -> str:
    return s["status"] + (f": {s['reason']}" if s.get("reason") else "")


def _interop(s: dict) -> str:
    i = s["interop"]
    unverified = i["status"] == "unchecked" and s["measuredBy"] == FUNCTION
    return (_step(i) + (f" (check {i['check']})" if i.get("check") else "")
            + (" — measured without an interop check" if unverified else ""))


def _unit(s: dict) -> str:
    shared = (f"; its function also holds {', '.join(s['sharedFunction'])}, measured with only this unit swapped"
              if s["sharedFunction"] else "")
    stays = f"; stayed on what they use: {', '.join(s['stayed'])}" if s["stayed"] else ""
    return f"- unit: {s['unit']}{shared}{stays}"


def _inputs(i: dict | None) -> str:
    if i is None:
        return "n/a (not in harness.yaml)"
    return f"input {i['inputSize'] or 'none'} B, key {i['keySize'] or 'none'} bits, from {i['from']}"


def _funnel(f: dict) -> list[str]:
    return ["| " + " | ".join(FUNNEL) + " |", "|" + "---|" * len(FUNNEL), "| " + " | ".join(str(f[k]) for k in FUNNEL) + " |"]


def _metric_lines(m: dict, units: dict) -> list[str]:
    """The time metric is one row in the latency unit and a throughput line under it, never two pieces of evidence."""
    name = f"{m['metric']}{SELECTED if m['selected'] else ''}"
    if not m["measured"]:
        return [f"| {name} ({m['unit']}) | {NOT_MEASURED}: {m['reason']} | | | |"]
    ratio = "n/a (zero before)" if m["ratio"] is None else f"{m['ratio']:.3f}"
    estimated = ", estimated" if m.get("kind") == ESTIMATED else ""
    shown = (m.get("views") or {}).get("latency") or {"unit": m["unit"], "before": m["before"], "after": m["after"]}
    lines = [f"| {name} ({shown['unit']}{estimated}) | {number(shown['before'])} → {number(shown['after'])} | {ratio} | {_p(m)} "
             f"| {m['n']} |"]
    if "views" in m:
        t = (m["views"] or {}).get("throughput")
        lines.append(f"| throughput ({units['throughput']}) | {number(t['before'])} → {number(t['after'])} | | | |" if t
                     else f"| throughput ({units['throughput']}) | {NOT_MEASURED}: no input size | | | |")
    return lines


def _recommended(doc: dict) -> list[str]:
    """Candidates above maxChange, reported and never applied; a report without any says nothing."""
    rows = doc.get("recommendations") or []
    if not rows and not doc.get("rejected"):
        return []
    lines = ["## Recommendations", "", f"maxChange: {doc['maxChange']}; these are not applied."]
    lines += [f"- {n['scope']}: {n['item']}: {n['change']} (input {n['diff']['input']}, key {n['diff']['key']}, "
              f"output {n['diff']['output']}, reach {n['diff']['reach']}"
              + (", adds a dependency" if n["diff"].get("addsDependency") else "") + ")" for n in rows]
    rejected = ", ".join(f"{k} {v}" for k, v in doc["rejected"].items())
    return lines + ([f"- rejected candidates: {rejected}"] if rejected else []) + [""]


def _chose(s: dict) -> str:
    named = (f", deciding {', '.join(s['deciding'])}" if s["deciding"] else "") + (f", accepted {', '.join(s['accepted'])}" if s["accepted"] else "")
    return named


def _thermal(s: dict) -> list[str]:
    t = s["thermal"]
    if t is None:
        return []
    sleeps = f"{t['before']['thermalThrottleSleepSeconds'] or 0} s before, {t['after']['thermalThrottleSleepSeconds'] or 0} s after"
    return [f"- thermal: start gap {t['startGap'] if t['startGap'] is not None else 'n/a'} degrees, thermal pause {sleeps}"
            + (f"; {', '.join(t['labels'])}" if t["labels"] else "")]


def _measured_by(s: dict) -> list[str]:
    """Which kind of number the table and verdict below are, and each kind against the dossier's estimate."""
    by = s["measuredBy"]
    said = {FUNCTION: "the function", CALL_SITE: "the swapped call alone, the function has no number; no interop check ran on it", None: NOT_MEASURED}[by]
    lines = [f"- measured by: {by or 'none'}: {said}"]
    for name, kind in s["measurements"].items():
        compared = "; ".join(f"{c['metric']} {c['ratio'] if c['ratio'] is None else round(c['ratio'], 3)} {c['change']}, estimated "
                             f"{[round(r, 3) for r in c['estimatedRatios']]}" for c in kind["truth"]["compared"])
        lines.append(f"- {name}: {kind['verdict']}, {kind['label']}; truth check {kind['truth']['verdict']}" + (f": {compared}" if compared else ""))
    return lines


def _swap(s: dict) -> list[str]:
    labels = ", ".join(f"{k} {v}" for k, v in s["labels"].items())
    lines = [f"- {s['current']} → {s['option']}: {', '.join(s['apps'])}; {labels}"]
    return lines + [f"  - {name}: median ratio {m['medianRatio']:.3f} over {len(m['ratios'])} apps, {m['scopes']} scopes"
                    for name, m in s["metrics"].items()]


def report_markdown(doc: dict) -> str:
    out = [f"# {doc['app']}: replacement report", "", f"Project: {doc['project']}. Source: {doc['source'] or 'n/a'}.", "",
           f"Mode: {doc['mode']}. Measured from: "
           f"{doc['measuredFrom'] or NOT_MEASURED}.", "", "## Funnel", "", *_funnel(doc["funnel"]), "",
           *_recommended(doc), "## Scopes"]
    for s in doc["scopes"]:
        d = s["decision"]
        out += ["", f"### {s['file']}:{s['line']} `{s['function']}` ({s['scope']})", "",
                _unit(s), f"- pattern: {s['pattern']} ({s['patternReason']}: {rule_words(s['patternReason'])})"
                + (f"; category_mismatch on {', '.join(s['categoryMismatch'])}" if s["categoryMismatch"] else ""),
                f"- current → option: {s['current'] or 'n/a'} → {s['option'] or 'n/a'}",
                f"- inputs: {_inputs(s['inputs'])}", *_measured_by(s),
                f"- decision: {d['decision']} ({d['source'] or 'n/a'}): {d['reason']}"
                + (" — stale: decided on an earlier dossier, `--refresh` asks again" if d["stale"] else ""),
                f"- edit: {_step(s['edit'])}", f"- compile: {_step(s['compile'])}",
                f"- interop: {_interop(s)}",
                f"- verdict ({doc['mode']}): {s['verdict']}; label: {s['label']}{_chose(s)}; `*` marks the metrics it selects",
                *_thermal(s), "",
                "| metric | before → after | ratio | pImprove | n |", "|---|---|---|---|---|"]
        for m in s["metrics"]:
            out += _metric_lines(m, doc["units"])
        if s["primitive"] and not any(m["measured"] for m in s["metrics"]):
            out += ["", "Primitive-only evidence (the benchmark's cases, not this function):"]
            out += [f"- {e['metric']} at {e['configuration']}: ratio {e['ratio']:.3f}, pImprove "
                    f"{'n/a (n<2)' if e['pImprove'] is None else format(e['pImprove'], '.2f')}" for e in s["primitive"]]
    return "\n".join(out) + "\n"


def _apps(doc: dict) -> list[str]:
    t = doc["thermal"]
    return ["", "## Apps", "", *(f"- {app}: {n['project']}, {n['source'] or 'n/a'}, {doc['modes'][app]}" for app, n in doc["named"].items()),
            "", f"Thermal: {t[THERMAL_MISMATCH]} pairs {THERMAL_MISMATCH}, {t[THERMAL_THROTTLED]} pairs {THERMAL_THROTTLED}."]


_COUNTS = (*PATTERNS, "unknownDefault", "categoryMismatch")


def _patterns(p: dict) -> list[str]:
    rows = [*p["byApp"].items(), ("all", p["all"])]
    return ["", "## Categories", "", "| app | " + " | ".join(_COUNTS) + " |", "|---|" + "---|" * len(_COUNTS),
            *(f"| {app} | " + " | ".join(str(c[k]) for k in _COUNTS) + " |" for app, c in rows)]


def _category(doc: dict, pattern: str) -> list[str]:
    """One category's labels, metrics and swaps; the two are never summed."""
    out = ["", f"## Category {pattern}", "", "Decisions by measured label: "
           + ", ".join(f"{k} {v}" for k, v in doc["labels"][pattern].items()) + ".",
           "", "| metric | " + " | ".join(CHANGES) + " | median change |", "|---|" + "---|" * (len(CHANGES) + 1)]
    out += [_metric_row(metric, m) for metric, m in doc["metrics"][pattern].items()]
    swaps = [s for s in doc["swaps"] if s["pattern"] == pattern]
    return out + (["", "Swaps:", "", *(line for s in swaps for line in _swap(s))] if swaps else [])


def _metric_row(metric: str, m: dict) -> str:
    change = NOT_MEASURED if m["medianChange"] is None else f"{m['medianChange']:+.1%}"
    estimated = f", estimated in {', '.join(m['estimatedIn'])}" if m.get("estimatedIn") else ""
    return f"| {metric} ({m['unit']}{estimated}) | " + " | ".join(str(len(m["apps"][c])) for c in CHANGES) + f" | {change} |"


def summary_markdown(doc: dict) -> str:
    modes = ", ".join(sorted(set(doc["modes"].values())))
    out = [f"# Replacement summary: {len(doc['apps'])} apps", "",
           f"Modes: {modes}, the metrics they select below, each app under its own. An app's change is the median ratio (after ÷ before) of its measured scopes; "
           f"improved at or below {doc['improvingRatio']}, worse at or above {1 / doc['improvingRatio']:.3f}.", "",
           "## Funnel", "", "| app | " + " | ".join(FUNNEL) + " |", "|---|" + "---|" * len(FUNNEL)]
    rows = [*doc["byApp"].items(), ("all", doc["funnel"])]
    out += [f"| {app} | " + " | ".join(str(f[k]) for k in FUNNEL) + " |" for app, f in rows]
    out += _apps(doc) + _patterns(doc["patterns"])
    for pattern in PATTERNS:
        out += _category(doc, pattern)
    if doc.get("recommendations") or doc.get("rejected"):
        counts = ", ".join(f"{k} {v}" for k, v in {**doc["recommendations"], **doc["rejected"]}.items())
        out += ["", "## Candidates not offered", "", f"Recommended above maxChange, never applied, and rejected: {counts}."]
    return "\n".join(out) + "\n"
