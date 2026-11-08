"""report.json and summary.json rendered as Markdown; numbers come only from the document."""
from __future__ import annotations

from ..dto.pattern import PATTERNS, rule_words
from ..dto.report import FUNNEL


def _step(s: dict) -> str:
    return s["status"] + (f": {s['reason']}" if s.get("reason") else "")


def _interop(s: dict) -> str:
    i = s["interop"]
    return _step(i) + (f" (check {i['check']})" if i.get("check") else "")


def _unit(s: dict) -> str:
    shared = f"; its function also holds {', '.join(s['sharedFunction'])}" if s["sharedFunction"] else ""
    stays = f"; stayed on what they use: {', '.join(s['stayed'])}" if s["stayed"] else ""
    return f"- unit: {s['unit']}{shared}{stays}"


def _inputs(i: dict | None) -> str:
    if i is None:
        return "n/a (not in harness.yaml)"
    return f"input {i['inputSize'] or 'none'} B, key {i['keySize'] or 'none'} bits, from {i['from']}"


def _funnel(f: dict) -> list[str]:
    return ["| " + " | ".join(FUNNEL) + " |", "|" + "---|" * len(FUNNEL), "| " + " | ".join(str(f[k]) for k in FUNNEL) + " |"]


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
    return (f"deciding {', '.join(s['deciding'])}" if s["deciding"] else "") + (
        f"{'; ' if s['deciding'] else ''}accepted {', '.join(s['accepted'])}" if s["accepted"] else "")


def report_markdown(doc: dict) -> str:
    out = [f"# {doc['app']}: replacement report", "", f"Project: {doc['project']}. Source: {doc['source'] or 'n/a'}.", "",
           f"Mode: {doc['mode']}.", "", "## Funnel", "", *_funnel(doc["funnel"]), "", *_recommended(doc), "## Scopes"]
    for s in doc["scopes"]:
        d = s["decision"]
        chose = _chose(s)
        out += ["", f"### {s['file']}:{s['line']} `{s['function']}` ({s['scope']})", "",
                _unit(s), f"- pattern: {s['pattern']} ({s['patternReason']}: {rule_words(s['patternReason'])})",
                f"- current → option: {s['current'] or 'n/a'} → {s['option'] or 'n/a'}",
                f"- inputs: {_inputs(s['inputs'])}",
                f"- decision: {d['decision']} ({d['source'] or 'n/a'}): {d['reason']}",
                *([f"- metrics: {chose}"] if chose else []),
                f"- edit: {_step(s['edit'])}", f"- compile: {_step(s['compile'])}", f"- interop: {_interop(s)}"]
        if s["primitive"]:
            out += ["", "Primitive evidence (the benchmark's cases, measured before the recommendation):"]
            out += [f"- {e['metric']} at {e['configuration']}: ratio {e['ratio']:.3f}, pImprove "
                    f"{'n/a (n<2)' if e['pImprove'] is None else format(e['pImprove'], '.2f')}" for e in s["primitive"]]
    return "\n".join(out + _broken_uses(doc)) + "\n"


def _broken_uses(doc: dict) -> list[str]:
    """Each broken use found and what it became; an upgraded row's returned output is still a reading, shown as review."""
    uses = doc["brokenUses"]
    if not uses["rows"]:
        return []
    return ["", "## Broken uses", "", ", ".join(f"{k} {v}" for k, v in uses["counts"].items()) + ".", "",
            "| site | current | became | option | source | needs | review |", "|---|---|---|---|---|---|---|",
            *(f"| {r['file']}:{r['line']} {r['function']} | {r['current']} | {r['status']} | {r['option'] or '-'} | {r['source']} "
              f"| {', '.join(r['needs']) or r['reason'] if r['status'] != 'upgraded' else '-'} | {', '.join(r['review']) or '-'} |" for r in uses["rows"])]


def _apps(doc: dict) -> list[str]:
    return ["", "## Apps", "", *(f"- {app}: {n['project']}, {n['source'] or 'n/a'}, {doc['modes'][app]}" for app, n in doc["named"].items())]


_COUNTS = (*PATTERNS, "unknownDefault")


def _patterns(p: dict) -> list[str]:
    rows = [*p["byApp"].items(), ("all", p["all"])]
    return ["", "## Categories", "", "| app | " + " | ".join(_COUNTS) + " |", "|---|" + "---|" * len(_COUNTS),
            *(f"| {app} | " + " | ".join(str(c[k]) for k in _COUNTS) + " |" for app, c in rows)]


def summary_markdown(doc: dict) -> str:
    out = [f"# Replacement summary: {len(doc['apps'])} apps", "",
           "## Funnel", "", "| app | " + " | ".join(FUNNEL) + " |", "|---|" + "---|" * len(FUNNEL)]
    rows = [*doc["byApp"].items(), ("all", doc["funnel"])]
    out += [f"| {app} | " + " | ".join(str(f[k]) for k in FUNNEL) + " |" for app, f in rows]
    out += _apps(doc) + _patterns(doc["patterns"])
    broken = doc["brokenUses"]["all"]
    if any(broken.values()):
        out += ["", "## Broken uses", "", ", ".join(f"{k} {v}" for k, v in broken.items()) + "."]
    if doc.get("recommendations") or doc.get("rejected"):
        counts = ", ".join(f"{k} {v}" for k, v in {**doc["recommendations"], **doc["rejected"]}.items())
        out += ["", "## Candidates not offered", "", f"Recommended above maxChange, never applied, and rejected: {counts}."]
    return "\n".join(out) + "\n"
