"""Known-answer accuracy of the scoper: per pattern rule and link kind, the sites and links it reads right and the wrong ones."""
from __future__ import annotations

from dataclasses import dataclass, field

from ...dto.site import Scope
from ...dto.unit import Unit


@dataclass
class Tally:
    right: int = 0
    total: int = 0
    wrong: list[str] = field(default_factory=list)

    def line(self, name: str) -> str:
        return f"{name}: {self.right}/{self.total}" + (f" wrong: {'; '.join(self.wrong)}" if self.wrong else "")


def _rule(truth: dict) -> str:
    return truth.get("reason") or f"pattern {truth['pattern']}"


def pattern_accuracy(expected: dict[str, dict], read: dict[str, Scope | None]) -> dict[str, Tally]:
    """A site is right when its patternReason is the true reason, or, with no true reason, its pattern is the true one;
    a site the scoper left unscoped (None) is wrong."""
    out: dict[str, Tally] = {}
    for marker, truth in sorted(expected.items()):
        s, t = read[marker], out.setdefault(_rule(truth), Tally())
        ok = s is not None and (s.patternReason == truth["reason"] if truth.get("reason") else s.pattern == truth["pattern"])
        t.total += 1
        t.right += ok
        if not ok:
            said = "unscoped" if s is None else f"{s.patternReason} ({s.pattern})"
            t.wrong.append(f"{marker} read {said}" + (f", {truth['hard']}" if truth.get("hard") else ""))
    return out


def link_accuracy(expected: list[dict], read: dict[str, Scope | None], units: list[Unit]) -> dict[str, Tally]:
    """Per kind: the true links found, then every link the scoper made that is not true, counted as wrong."""
    marker = {s.id: m for m, s in read.items() if s is not None}
    made = {(k.kind, frozenset((marker.get(k.a), marker.get(k.b)))) for u in units for k in u.links}
    truth = {(e["kind"], frozenset((e["a"], e["b"]))) for e in expected}
    out: dict[str, Tally] = {}
    for kind, pair in sorted(truth | made, key=lambda x: (x[0], sorted(map(str, x[1])))):
        t = out.setdefault(kind, Tally())
        names = " ".join(sorted(map(str, pair)))
        if (kind, pair) in truth:
            t.total += 1
            t.right += (kind, pair) in made
            if (kind, pair) not in made:
                t.wrong.append(f"missed {names}")
        else:
            t.wrong.append(f"extra {names}")
    return out
