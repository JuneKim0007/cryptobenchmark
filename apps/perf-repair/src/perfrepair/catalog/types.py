"""The type facts of the algorithm catalogues, looked up by family and canonical name; strength at a key size."""
from __future__ import annotations

from dataclasses import dataclass
from functools import cache

from ..dto.types import Properties, Strength, TypeRow
from .algorithms import (
    AUTHENTICATED,
    DETERMINISTIC,
    MIN_SDK,
    NONCE,
    OUTPUT,
    PARAMETERS,
    STRENGTH,
    Algorithms,
    Entry,
    algorithms,
)
from .names import fold


@dataclass(frozen=True)
class Types:
    rows: dict[tuple[str, str], TypeRow]
    key_strength: dict[str, dict[int, int]]
    deterministic_relied: frozenset[str]
    sources: dict[str, str]

    def of(self, family: str, canonical: str | None) -> TypeRow | None:
        return self.rows.get((family, fold(canonical))) if canonical else None

    def strength(self, row: TypeRow, key_size: int | None) -> int | None:
        """The row's strength at a key size; a key-size fact without the size is None."""
        s = row.strength
        if s.bits is not None:
            return s.bits
        if s.key is None or key_size is None:
            return None
        table = self.key_strength[s.key]
        below = [bits for size, bits in table.items() if size <= key_size]
        bits = max(below) if below else 0
        return min(bits, s.cap) if s.cap is not None else bits


def _strength(raw) -> Strength:
    if raw is None:
        return Strength()
    if isinstance(raw, dict):
        return Strength(key=raw["key"], cap=raw.get("cap"))
    return Strength(bits=raw)


def _row(entry: Entry) -> TypeRow:
    c, strength, min_sdk = entry.raw["conditions"], entry.sourced(STRENGTH), entry.sourced(MIN_SDK)
    props = Properties(c[AUTHENTICATED]["value"], c[DETERMINISTIC]["value"], entry.required(NONCE)["value"],
                       entry.required(PARAMETERS)["value"], c[OUTPUT]["bytes"], entry.raw["key"]["type"])
    return TypeRow(entry.family, entry.canonical, c[OUTPUT]["kind"], props, _strength(strength["value"]), strength["source"],
                   min_sdk["value"], min_sdk["source"])


def of_catalogues(catalogues: Algorithms) -> Types:
    """An entry without type facts has no row: the catalogue checked they come whole."""
    rows = {(e.family, fold(e.canonical)): _row(e) for e in catalogues.entries if e.sourced(STRENGTH) is not None}
    common = catalogues.common
    return Types(rows, common.key_strength, common.deterministic_relied, common.sources)


@cache
def types() -> Types:
    return of_catalogues(algorithms())
