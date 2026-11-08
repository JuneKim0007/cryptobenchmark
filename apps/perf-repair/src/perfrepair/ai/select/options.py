"""One option's lines in the replacement message: item, pins, change, interop and the risk it adds, code label, estimates."""
from __future__ import annotations

import re

from ...dto.dossier import Option, pin_text
from ...dto.grouping import algorithm_of, provider_of
from ...dto.replacement import required_risks
from ...dto.site import Scope
from ...result.configurations import parse_label
from ...result.gain import IMPROVED, WORSE, by_change, option_label

UNKNOWN_PINS = "unknown (no configuration measured on both sides); this option cannot be chosen"
TOO_FEW_RUNS = "n/a (n<2)"


def _interop(s: Scope, o: Option) -> str:
    added = [r for r in required_risks(s, o) if r not in required_risks(s)]
    return f"    interop: {o.interop}" + (f"; a replace to it must also declare {', '.join(added)}" if added else "")


def _change(o: Option) -> list[str]:
    """A drop-in shows nothing, so its prompt and evidence stay what they were before change classes."""
    if o.diff is None:
        return []
    return [f"    change: {o.change} | input {o.diff.input} | key {o.diff.key} | output {o.diff.output} | reach {o.diff.reach}"
            + (" | adds a dependency" if o.diff.addsDependency else "")]


def option_lines(s: Scope, o: Option) -> list[str]:
    pins = UNKNOWN_PINS if o.pins is None else ", ".join(f"{k}={pin_text(v)}" for k, v in o.pins.items()) or "none"
    lines = [f"  {o.alias} = {o.item} | name {algorithm_of(o.item)} | provider {provider_of(o.item)}", f"    pins: {pins}",
             *_change(o), _interop(s, o)]
    # a metric both sides have but no ratio is shown with its reason, never left out unexplained
    absent = [f"    no estimate: {n.metric} at {n.configuration}: {n.reason}" for n in o.noEstimates]
    if not o.estimates:
        return lines + ["    estimates: none measured", *absent]
    named = _names(o.estimates)
    lines += _review(o)
    cells = [f"{e.metric}{named[e.configuration]} {e.ratio:.3f} "
             f"{TOO_FEW_RUNS if e.pImprove is None else f'{e.pImprove:.3f}'} {e.n}" for e in o.estimates]
    # with no input size nothing is nearest: result/configurations.py nearest() keeps every measured size
    where = "every measured input size (this site's is unknown)" if s.inputSize is None else "the configurations nearest this site"
    return lines + [f"    estimates (ratio option ÷ current, pImprove, n), {where}: " + "; ".join(cells), *absent]


def _review(o: Option) -> list[str]:
    # needsReview: result/change.py's list, once it carries one
    needs = getattr(o, "needsReview", ())
    return [_label(o)] + ([f"    needs review: {', '.join(needs)}"] if needs else [])


def _label(o: Option) -> str:
    better, worse = by_change(o.estimates, IMPROVED), by_change(o.estimates, WORSE)
    said = [f"improved {', '.join(better)}"] * bool(better) + [f"worse {', '.join(worse)}"] * bool(worse)
    return f"    label: {option_label(o.estimates)}" + (f" ({'; '.join(said)})" if said else "")


def _names(estimates) -> dict[str, str]:
    """Each configuration as `@<input size>`, with the operation, key and phase only where they differ; the MEASURED
    lines carry them."""
    parsed = {e.configuration: parse_label(e.configuration) for e in estimates}
    if not all(parsed.values()):
        return {c: f" at {c}:" for c in parsed}
    varies = [f for f in ("op", "key", "phase") if len({m[f] for m in parsed.values()}) > 1]
    return {c: _name(m, varies) for c, m in parsed.items()}


def _name(m: re.Match, varies: list[str]) -> str:
    shown = "".join(f" key {m[f]}" if f == "key" else f" {m[f]}" for f in varies)
    return f"@{m['input']}{shown}" + (" (estimated)" if m["estimated"] else "")
