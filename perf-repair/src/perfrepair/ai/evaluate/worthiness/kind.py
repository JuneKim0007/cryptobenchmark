from __future__ import annotations

from pathlib import Path

from .... import run_dir as rd
from ....dto import GroupEvidence, Pair, Verdict, Verdicts
from ....dto.decision import OutboxRecord
from ....dto.prompt import Charter, TaskPrompt
from ....dto.worthiness import DECISIONS
from ....files import write_json
from ....result.confidence import describe
from ....result.modes import Mode
from ....result.triage import triage
from ....validation.json_reply import parse_object
from ....validation.worthiness import validate_verdicts
from ...runtime.engine.kind import project
from ...runtime.prompt import PromptLibrary

NAME = "evaluate/worthiness"

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



def _num(x: float | None, fmt: str = "{:.0f}") -> str:
    return "-" if x is None else fmt.format(x)


def aliases(e: GroupEvidence) -> dict[str, str]:
    """M1..Mn: member ids contain the table's column separator."""
    return {f"M{n}": m for n, m in enumerate(e.members, 1)}


def charter(library: PromptLibrary) -> Charter:
    return library.charter(NAME, SCHEMA)


class WorthinessKind:

    def __init__(self, mode: Mode, comparability: list[str], evidence: list[GroupEvidence], directory: Path):
        self.mode, self.comparability, self.evidence, self.directory = mode, comparability, evidence, Path(directory)
        self.name = f"worthiness-{mode.name}"
        self._ask, self.static = triage(evidence, mode)

    def items(self) -> list[GroupEvidence]:
        return self._ask

    def empty(self) -> Verdicts:
        return Verdicts(self.mode.name, 0, {v.groupId: v for v in self.static})

    def admit(self, e: GroupEvidence) -> list[str]:
        return []

    def label(self, e: GroupEvidence) -> str:
        return e.groupId

    def render(self, e: GroupEvidence, verdicts: Verdicts) -> TaskPrompt:
        lines = [f"MODE: {self.mode.name} — {self.mode.rule}", "RUN WARNINGS:"]
        lines += [f"  - {w}" for w in self.comparability] or ["  (none)"]
        lines += ["", f"GROUP {e.groupId} | {e.label} | {e.type} | family {e.family}"]
        alias = aliases(e)
        short = {m: a for a, m in alias.items()}
        lines += ["", "MEMBERS (answer with these names)"] + [f"  {a} = {m}" for a, m in alias.items()]
        for c in e.configurations:
            if not c.pairs:
                continue
            lines += ["", f"CONFIGURATION {c.operation} key {c.keySize} input {c.inputSize} {c.phase}",
                      "  member | median ns | median 95% interval (bootstrap) | p25 | p75 | cv | n | allocations/op"]
            for m in c.members:
                t = m.timeNs
                lines.append(f"  {short[m.itemId]} | " + (" | ".join([_num(t.median), f"{_num(t.low)}..{_num(t.high)}", _num(t.p25), _num(t.p75),
                             _num(t.cv, "{:.3f}"), str(t.n)]) if t else "not measured | | | | |")
                             + f" | {_num(m.allocations)}")
            lines.append("  pair from -> to | time ratio | pImprove (confidence) | n | allocation ratio | interop | improves")
            for p in c.pairs:
                lines.append(f"  {short[p.fromItem]} -> {short[p.toItem]} | {p.timeRatio:.3f} | {describe(p.pImprove)} | "
                             f"{p.n} | {_num(p.allocationRatio, '{:.3f}')} | {p.interop} | {self.mode.improves(p)}")
        return TaskPrompt(NAME, "\n".join(lines), e.key)

    def check(self, e: GroupEvidence, text: str, verdicts: Verdicts) -> tuple[dict | None, list[str]]:
        d, problems = parse_object(text)
        if d is None:
            return None, problems
        decision = d.get("decision")
        reason = d.get("reason").strip() if isinstance(d.get("reason"), str) else ""
        raw = d.get("pairs") if isinstance(d.get("pairs"), list) else None
        problems, pairs = [], []
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
            judged = [(self.mode.judge(m), m) for m in metrics if m.fromItem == a and m.toItem == b]
            hits = [m for j, m in judged if j == "improves"]
            if not hits:
                why_not = "lacks the measurements" if any(j == "not_measured" for j, _ in judged) else "does not improve"
                problems.append(f"pairs[{i}]: {b} {why_not} on {a} under {self.mode.name} in any configuration")
                continue
            # the pair carries its best-supported configuration; a low level is reported, never refused
            best = max(hits, key=lambda m: -1.0 if m.pImprove is None else m.pImprove)
            pairs.append(Pair(a, b, why, best.pImprove, best.level))
        if problems:
            return None, problems
        return Verdict(e.groupId, self.mode.name, decision, reason, "llm", self.mode.proxy, tuple(pairs)).to_json(), []

    def apply(self, verdicts: Verdicts, e: GroupEvidence, record: OutboxRecord) -> None:
        verdicts.verdicts[e.groupId] = (Verdict.from_json(record.decision) if record.outcome == "decided" else
                                        Verdict(e.groupId, self.mode.name, "skip", "dropped: " + "; ".join(record.problems),
                                                "fallback", self.mode.proxy))
        verdicts.version += 1

    def validate(self, verdicts: Verdicts, records: list[OutboxRecord]) -> list[str]:
        problems = validate_verdicts(verdicts, self.evidence, self.mode)
        if verdicts.version != len(records):
            problems.append(f"verdicts version {verdicts.version} is not the {len(records)} records committed")
        if project(self, records) != verdicts:
            problems.append("verdicts differ from triage plus the replay of the outbox")
        return problems

    def write(self, verdicts: Verdicts, records: list[OutboxRecord]) -> None:
        write_json(self.directory / rd.VERDICTS, verdicts.to_json())
