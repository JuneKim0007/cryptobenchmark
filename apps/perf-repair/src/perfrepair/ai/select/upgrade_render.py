"""What Select sees for one broken use: the site, sinks and reach, the current item, the ranked candidates."""
from __future__ import annotations

from ...dto.dossier import Option
from ...dto.grouping import algorithm_of, provider_of
from ...dto.upgrade import UpgradeItem
from ...result.change import reach
from ...result.gain import option_label


def _known(x) -> str:
    return "unknown" if x is None else str(x)


def _option(item: UpgradeItem, o: Option) -> list[str]:
    own = item.measured.get(o.item) or {}
    medians = ", ".join(f"{m} {v:.6g}" for m, v in own.items() if v is not None) or "none"
    lines = [f"  {o.alias} = {o.item} | name {algorithm_of(o.item)} | provider {provider_of(o.item)}",
             f"    change: {o.change}" + (f" | input {o.diff.input} | key {o.diff.key} | output {o.diff.output}" if o.diff else ""),
             f"    measured medians at this site: {medians}"]
    if o.estimates:
        ratios = "; ".join(f"{e.metric} {e.ratio:.3f} at {e.configuration}" for e in o.estimates)
        lines.append(f"    label: {option_label(o.estimates)} | ratio to the current: {ratios}")
    return lines


def render(item: UpgradeItem) -> str:
    d, s = item.dossier, item.dossier.scope
    lines = [f"SITE {s.file}:{s.line} | call {s.call} | function {s.function}",
             f"  engine type {s.engineType} | key size {_known(s.keySize)} | input size {_known(s.inputSize)}",
             "", "SCOPE FACTS", f"  sinks: {', '.join(s.sinks)}", f"  reach: {reach(s)}",
             "", f"CURRENT {d.current} | screening: {item.screenReason}", "", "CANDIDATES (best measured performance first; answer with one, none is not allowed: the current is broken)"]
    return "\n".join(lines + [line for o in d.options for line in _option(item, o)])
