"""report.json and summary.json rendered as Markdown; numbers come only from the document."""
from __future__ import annotations

from ..dto.measurement import ESTIMATED
from ..dto.report import CHANGES, FUNNEL
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
    unverified = i["status"] == "unchecked" and any(m["measured"] for m in s["metrics"])
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


def report_markdown(doc: dict) -> str:
    out = [f"# {doc['app']}: replacement report", "", f"Mode: {doc['mode']}. Measured from: "
           f"{doc['measuredFrom'] or NOT_MEASURED}.", "", "## Funnel", "", *_funnel(doc["funnel"]), "", "## Scopes"]
    for s in doc["scopes"]:
        d = s["decision"]
        out += ["", f"### {s['file']}:{s['line']} `{s['function']}` ({s['scope']})", "",
                _unit(s), f"- current → option: {s['current'] or 'n/a'} → {s['option'] or 'n/a'}",
                f"- inputs: {_inputs(s['inputs'])}",
                f"- decision: {d['decision']} ({d['source'] or 'n/a'}): {d['reason']}"
                + (" — stale: decided on an earlier dossier, `--refresh` asks again" if d["stale"] else ""),
                f"- edit: {_step(s['edit'])}", f"- compile: {_step(s['compile'])}",
                f"- interop: {_interop(s)}",
                f"- verdict ({doc['mode']}): {s['verdict']}; `*` marks the metrics it selects", "",
                "| metric | before → after | ratio | pImprove | n |", "|---|---|---|---|---|"]
        for m in s["metrics"]:
            out += _metric_lines(m, doc["units"])
        if s["primitive"] and not any(m["measured"] for m in s["metrics"]):
            out += ["", "Primitive-only evidence (the benchmark's cases, not this function):"]
            out += [f"- {e['metric']} at {e['configuration']}: ratio {e['ratio']:.3f}, pImprove "
                    f"{'n/a (n<2)' if e['pImprove'] is None else format(e['pImprove'], '.2f')}" for e in s["primitive"]]
    return "\n".join(out) + "\n"


def summary_markdown(doc: dict) -> str:
    out = [f"# Replacement summary: {len(doc['apps'])} apps", "",
           f"Mode: {doc['mode']}, its selected metrics below. An app's change is the median ratio (after ÷ before) of its measured scopes; "
           f"improved at or below {doc['improvingRatio']}, worse at or above {1 / doc['improvingRatio']:.3f}.", "",
           "## Funnel", "", "| app | " + " | ".join(FUNNEL) + " |", "|---|" + "---|" * len(FUNNEL)]
    rows = [*doc["byApp"].items(), ("all", doc["funnel"])]
    out += [f"| {app} | " + " | ".join(str(f[k]) for k in FUNNEL) + " |" for app, f in rows]
    out += ["", "## Metrics", "", "| metric | " + " | ".join(CHANGES) + " | median change |", "|---|" + "---|" * (len(CHANGES) + 1)]
    for metric, m in doc["metrics"].items():
        change = NOT_MEASURED if m["medianChange"] is None else f"{m['medianChange']:+.1%}"
        estimated = f", estimated in {', '.join(m['estimatedIn'])}" if m.get("estimatedIn") else ""
        out.append(f"| {metric} ({m['unit']}{estimated}) | " + " | ".join(str(len(m["apps"][c])) for c in CHANGES) + f" | {change} |")
    return "\n".join(out) + "\n"
