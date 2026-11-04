"""Producer → consumer: a key-making object's output reaching another object's key requirement, by the line it is made
on, or in one class by a helper's call, a field it is written to, or a parameter of the type the helper returns."""
from __future__ import annotations

import re
from dataclasses import dataclass

from ...dto.lifecycle import Requirement
from ...dto.site import Scope
from ...dto.unit import PRODUCER_CONSUMER, Link
from .relations import Relations
from .shapes import Files, Shape

_MADE = frozenset(("generated", "derived"))
_WRITTEN = re.compile(r"^\s*(?:this\.)?(\w+)\s*=[^=]")
RETURNED = "return"


def key_requirements(s: Scope) -> list[Requirement]:
    return [r for r in s.lifecycle.requirements if r.name == "key"]


def _family_fits(producer: Scope, consumer: Scope) -> bool:
    """Only the parameter rule needs it: nothing else ties the two; an unknown name cannot rule the pair out."""
    if producer.algorithm is None or consumer.algorithm is None:
        return True
    return consumer.algorithm.split("/")[0].upper() == producer.algorithm.upper()


@dataclass(frozen=True)
class _Pair:
    producer: Scope
    consumer: Scope
    made: Shape
    takes: Shape
    lines: tuple[int, ...]
    files: Files

    def _returned(self) -> str | None:
        return self.made.returns if RETURNED in self.producer.sinks else None

    def _by_call(self, r: Requirement) -> bool:
        called = re.search(rf"\b{re.escape(self.producer.function)}\s*\(", self.files.text(self.consumer.file, r.line))
        return r.origin == "same_class_call" and called is not None and self._returned() is not None

    def _by_field(self, r: Requirement) -> bool:
        if r.origin != "field" or not _MADE & set(r.depth1):
            return False
        declared = self.files.text(self.consumer.file, r.line)
        written = [_WRITTEN.match(self.files.text(self.producer.file, n)) for n in self.lines]
        return any(m is not None and re.search(rf"\b{m.group(1)}\b", declared) is not None for m in written)

    def _by_parameter(self, r: Requirement) -> bool:
        returned = self._returned()
        return (r.origin == "parameter" and returned is not None and _family_fits(self.producer, self.consumer)
                and any(type_ == returned for _, type_ in self.files.parameters_taken(self.consumer, r)))

    def _reaches(self, r: Requirement) -> str | None:
        if r.line in self.lines and r.origin in _MADE:
            return "line"
        if self.made.owner is None or self.made.owner != self.takes.owner:
            return None
        checks = (("call", self._by_call), ("field", self._by_field), ("parameter", self._by_parameter))
        return next((via for via, reaches in checks if reaches(r)), None)

    def link(self) -> Link | None:
        for r in key_requirements(self.consumer):
            via = self._reaches(r)
            if via:
                return Link(PRODUCER_CONSUMER, self.producer.id, self.consumer.id, self.lines, (r.line, r.at), via)
        return None


def consumer_links(scopes: list[Scope], relations: Relations, files: Files) -> list[Link]:
    out = []
    for p in scopes:
        lines = relations.output_lines(p)
        if not lines:
            continue
        for c in scopes:
            if c.id != p.id and key_requirements(c):
                link = _Pair(p, c, files.shape(p), files.shape(c), lines, files).link()
                if link:
                    out.append(link)
    return out
