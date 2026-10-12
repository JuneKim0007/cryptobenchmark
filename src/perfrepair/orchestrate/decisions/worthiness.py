"""Decision: is replacing one primitive with another in its group worth testing in an app?

The model sees one group's evidence (every number computed by code), the mode, and the run's
comparability warnings, and answers test or skip. The gate refuses a pair that names a primitive
outside the group, or that the mode says does not improve in any configuration.
"""
from __future__ import annotations

import json
from pathlib import Path

from ...dto import GroupEvidence, Pair, Verdict, Verdicts
from ...dto.worthiness import DECISIONS
from ...files import read_json
from ...result.modes import Mode
from .kind import Checked

PROMPT = Path(__file__).parents[1] / "prompts" / "worthiness.system.md"

SCHEMA = {
    "type": "object",
    "properties": {
        "decision": {"type": "string", "enum": list(DECISIONS)},
        "pairs": {"type": "array", "items": {
            "type": "object",
            "properties": {"from": {"type": "string"}, "to": {"type": "string"}, "reason": {"type": "string"}},
            "required": ["from", "to", "reason"],
            "additionalProperties": False,
        }},
        "reason": {"type": "string"},
    },
    "required": ["decision", "pairs", "reason"],
    "additionalProperties": False,
}


def open_verdicts(path: Path, mode: Mode) -> Verdicts:
    if Path(path).exists():
        verdicts = Verdicts.from_json(read_json(path))
        if verdicts.mode != mode.name:
            raise ValueError(f"{path}: verdicts for mode {verdicts.mode!r}, not {mode.name!r}")
        return verdicts
    return Verdicts(mode.name)


def _num(x: float | None, fmt: str = "{:.0f}") -> str:
    return "-" if x is None else fmt.format(x)


def aliases(e: GroupEvidence) -> dict[str, str]:
    """M1..Mn for the group's members in sorted order; ids contain the table's column separator."""
    return {f"M{n}": m for n, m in enumerate(e.members, 1)}


class WorthinessKind:
    schema = SCHEMA

    def __init__(self, mode: Mode, comparability: list[str], prompt: str | None = None,
                 name: str = "worthiness"):
        self.mode, self.comparability, self.name = mode, comparability, name
        self.prompt = prompt if prompt is not None else PROMPT.read_text()

    def render(self, e: GroupEvidence, verdicts: Verdicts, refused: list[str] | None) -> str:
        lines = [f"MODE: {self.mode.name} — {self.mode.rule}", "RUN WARNINGS:"]
        lines += [f"  - {w}" for w in self.comparability] or ["  (none)"]
        lines += ["", f"GROUP {e.itemId} | {e.label} | {e.type} | family {e.family}"]
        alias = aliases(e)
        short = {m: a for a, m in alias.items()}
        lines += ["", "MEMBERS (answer with these names)"] + [f"  {a} = {m}" for a, m in alias.items()]
        for c in e.configurations:
            if not c.pairs:
                continue
            lines += ["", f"CONFIGURATION {c.operation} key {c.keySize} input {c.inputSize} {c.phase}",
                      "  member | median ns | p25 | p75 | cv | n | allocations/op"]
            for m in c.members:
                t = m.timeNs
                lines.append(f"  {short[m.itemId]} | " + (" | ".join([_num(t.median), _num(t.p25), _num(t.p75),
                             _num(t.cv, "{:.3f}"), str(t.n)]) if t else "not measured | | | |")
                             + f" | {_num(m.allocations)}")
            lines.append("  pair from -> to | time ratio | IQR overlap | allocation ratio | improves")
            for p in c.pairs:
                lines.append(f"  {short[p.fromItem]} -> {short[p.toItem]} | {p.timeRatio:.3f} | {p.iqrOverlap} | "
                             f"{_num(p.allocationRatio, '{:.3f}')} | {self.mode.improves(p)}")
        if refused:
            lines += ["", "YOUR PREVIOUS ANSWER WAS REFUSED:"] + [f"  - {p}" for p in refused]
        return "\n".join(lines)

    def validate(self, e: GroupEvidence, text: str, verdicts: Verdicts) -> Checked:
        try:
            d = json.loads(text)
        except json.JSONDecodeError as err:
            return Checked(problems=[f"reply is not JSON: {err}"])
        if not isinstance(d, dict):
            return Checked(problems=["reply is not an object"])
        decision = d.get("decision")
        reason = d.get("reason").strip() if isinstance(d.get("reason"), str) else ""
        raw = d.get("pairs") if isinstance(d.get("pairs"), list) else None
        problems, warnings, pairs = [], [], []
        if decision not in DECISIONS:
            problems.append(f"decision {decision!r} is not one of {DECISIONS}")
        if not reason:
            problems.append("reason is empty")
        if raw is None:
            problems.append("pairs is not a list")
            raw = []
        if decision == "test" and not raw:
            problems.append("test names no pair")
        if decision == "skip" and raw:
            problems.append("skip names pairs; a skip has none")
        alias = aliases(e)
        metrics = [p for c in e.configurations for p in c.pairs]
        for i, p in enumerate(raw):
            if not isinstance(p, dict):
                problems.append(f"pairs[{i}] is not an object")
                continue
            why = p.get("reason").strip() if isinstance(p.get("reason"), str) else ""
            if p.get("from") not in alias or p.get("to") not in alias or p.get("from") == p.get("to"):
                problems.append(f"pairs[{i}]: {p.get('from')!r} -> {p.get('to')!r} is not two different members "
                                f"({', '.join(alias)})")
                continue
            a, b = alias[p["from"]], alias[p["to"]]
            if not why:
                problems.append(f"pairs[{i}]: reason is empty")
            hits = [m for m in metrics if m.fromItem == a and m.toItem == b and self.mode.improves(m)]
            if not hits:
                problems.append(f"pairs[{i}]: {b} does not improve on {a} under {self.mode.name} in any configuration")
            elif all(m.iqrOverlap for m in hits):
                warnings.append(f"pairs[{i}]: every improving configuration overlaps in IQR")
            pairs.append(Pair(a, b, why))
        if problems:
            return Checked(problems=problems, warnings=warnings)
        return Checked(Verdict(e.itemId, self.mode.name, decision, reason, "llm", self.mode.proxy, tuple(pairs)),
                       warnings=warnings)

    def apply(self, e: GroupEvidence, verdict: Verdict, verdicts: Verdicts) -> dict:
        verdicts.verdicts[e.itemId] = verdict
        verdicts.version += 1
        return {"groupId": e.itemId, "decision": verdict.decision}

    def fallback(self, e: GroupEvidence, problems: list[str]) -> Verdict:
        return Verdict(e.itemId, self.mode.name, "skip", "every answer was refused: " + "; ".join(problems),
                       "fallback", self.mode.proxy)

    def decision_json(self, verdict: Verdict) -> dict:
        return verdict.to_json()

    def decision_from_json(self, doc: dict) -> Verdict:
        return Verdict.from_json(doc)
