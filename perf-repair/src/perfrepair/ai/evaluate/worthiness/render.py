"""What the worthiness decision sees for one group: mode, run warnings, aliased members, per-configuration tables."""
from __future__ import annotations

from ....dto import GroupEvidence
from ....result.confidence import describe
from ....result.modes import Mode
from ....validation.evaluate.worthiness import aliases


def _num(x: float | None, fmt: str = "{:.0f}") -> str:
    return "-" if x is None else fmt.format(x)


def render(e: GroupEvidence, mode: Mode, comparability: list[str]) -> str:
    lines = [f"MODE: {mode.name} — {mode.rule}", "RUN WARNINGS:"]
    lines += [f"  - {w}" for w in comparability] or ["  (none)"]
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
                         f"{p.n} | {_num(p.allocationRatio, '{:.3f}')} | {p.interop} | {mode.improves(p)}")
    return "\n".join(lines)
