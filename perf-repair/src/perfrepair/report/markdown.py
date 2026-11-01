"""report.json and summary.json rendered as Markdown; numbers come only from the document."""
from __future__ import annotations

from ..dto.report import CHANGES, FUNNEL

NOT_MEASURED = "not measured"


def _num(v: float | None, digits: int = 3) -> str:
    return "n/a" if v is None else f"{v:.{digits}g}" if abs(v) < 1000 else f"{v:,.0f}"


def _p(m: dict) -> str:
    return "n/a (n<2)" if m["pImprove"] is None else f"{m['pImprove']:.2f} ({m['level']})"


def _step(s: dict) -> str:
    return s["status"] + (f": {s['reason']}" if s.get("reason") else "")


def _funnel(f: dict) -> list[str]:
    return ["| " + " | ".join(FUNNEL) + " |", "|" + "---|" * len(FUNNEL), "| " + " | ".join(str(f[k]) for k in FUNNEL) + " |"]


def _metric_lines(m: dict) -> list[str]:
    if not m["measured"]:
        return [f"| {m['metric']} ({m['unit']}) | {NOT_MEASURED}: {m['reason']} | | | |"]
    ratio = "n/a (zero before)" if m["ratio"] is None else f"{m['ratio']:.3f}"
    lines = [f"| {m['metric']} ({m['unit']}) | {_num(m['before'])} → {_num(m['after'])} | {ratio} | {_p(m)} | {m['n']} |"]
    t = m.get("throughput")
    if t:
        ops = t["opsPerSecond"]
        lines.append(f"| ops/s | {_num(ops['before'])} → {_num(ops['after'])} | | | |")
        mb = t["mbPerSecond"]
        lines.append(f"| MB/s | {_num(mb['before'])} → {_num(mb['after'])} | | | |" if mb
                     else f"| MB/s | {NOT_MEASURED}: no input size | | | |")
    return lines


def report_markdown(doc: dict) -> str:
    out = [f"# {doc['app']}: replacement report", "", f"Mode: {doc['mode']}. Measured from: "
           f"{doc['measuredFrom'] or NOT_MEASURED}.", "", "## Funnel", "", *_funnel(doc["funnel"]), "", "## Scopes"]
    for s in doc["scopes"]:
        d = s["decision"]
        out += ["", f"### {s['file']}:{s['line']} `{s['function']}` ({s['scope']})", "",
                f"- current → option: {s['current'] or 'n/a'} → {s['option'] or 'n/a'}",
                f"- decision: {d['decision']} ({d['source'] or 'n/a'}): {d['reason']}",
                f"- edit: {_step(s['edit'])}", f"- compile: {_step(s['compile'])}",
                f"- interop: {_step(s['interop'])}" + (f" (check {s['interop']['check']})" if s["interop"].get("check") else ""),
                f"- verdict ({doc['mode']}): {s['verdict']}", "",
                "| metric | before → after | ratio | pImprove | n |", "|---|---|---|---|---|"]
        for m in s["metrics"]:
            out += _metric_lines(m)
        if s["primitive"] and not any(m["measured"] for m in s["metrics"]):
            out += ["", "Primitive-only evidence (the benchmark's cases, not this function):"]
            out += [f"- {e['metric']} at {e['configuration']}: ratio {e['ratio']:.3f}, pImprove "
                    f"{'n/a (n<2)' if e['pImprove'] is None else format(e['pImprove'], '.2f')}" for e in s["primitive"]]
    return "\n".join(out) + "\n"


def summary_markdown(doc: dict) -> str:
    out = [f"# Replacement summary: {len(doc['apps'])} apps", "",
           f"Mode: {doc['mode']}. An app's change is the median ratio (after ÷ before) of its measured scopes; "
           f"improved at or below {doc['improvingRatio']}, worse at or above {1 / doc['improvingRatio']:.3f}.", "",
           "## Funnel", "", "| app | " + " | ".join(FUNNEL) + " |", "|---|" + "---|" * len(FUNNEL)]
    rows = [*doc["byApp"].items(), ("all", doc["funnel"])]
    out += [f"| {app} | " + " | ".join(str(f[k]) for k in FUNNEL) + " |" for app, f in rows]
    out += ["", "## Metrics", "", "| metric | " + " | ".join(CHANGES) + " | median change |", "|---|" + "---|" * (len(CHANGES) + 1)]
    for metric, m in doc["metrics"].items():
        change = NOT_MEASURED if m["medianChange"] is None else f"{m['medianChange']:+.1%}"
        out.append(f"| {metric} ({m['unit']}) | " + " | ".join(str(len(m["apps"][c])) for c in CHANGES) + f" | {change} |")
    return "\n".join(out) + "\n"
