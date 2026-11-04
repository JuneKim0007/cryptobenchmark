"""catalog/types.yaml: read, checked whole (every field, every source, every family), and looked up by family and name."""
from __future__ import annotations

from dataclasses import dataclass, fields
from functools import cache
from pathlib import Path

import yaml

from ..dto.coded import InputError
from ..dto.document import AT_PATH, DocumentKind
from ..dto.types import NONCES, OUTPUT_KINDS, Properties, Strength, TypeRow
from .families import Families
from .names import fold

CATALOG = Path(__file__).with_name("types.yaml")
SCHEMA_VERSION = 1
UNSOURCED = "unsourced"
PROPERTY_FIELDS = tuple(f.name for f in fields(Properties))
ROW_FIELDS = {"outputKind", *PROPERTY_FIELDS, "strengthBits", "strengthSource", "minSdk", "minSdkSource"}


class TypesError(InputError):
    pass


TYPES_DOC = DocumentKind("types", SCHEMA_VERSION, "types_schema: " + AT_PATH, TypesError)


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


def _strength(raw, where: str) -> Strength:
    if raw is None:
        return Strength()
    if isinstance(raw, int) and not isinstance(raw, bool):
        return Strength(bits=raw)
    if isinstance(raw, dict) and set(raw) <= {"key", "cap"} and "key" in raw:
        return Strength(key=raw["key"], cap=raw.get("cap"))
    raise TypesError(f"types_strength: {where}: {raw!r} is neither bits, {{key, cap}} nor null")


def _row(family: str, canonical: str, raw: dict) -> TypeRow:
    where = f"{family} {canonical}"
    missing, stray = ROW_FIELDS - set(raw), set(raw) - ROW_FIELDS
    if missing or stray:
        raise TypesError(f"types_fields: {where}: missing {sorted(missing)}, unknown {sorted(stray)}")
    props = Properties(**{k: raw[k] for k in PROPERTY_FIELDS})
    return TypeRow(family, canonical, raw["outputKind"], props, _strength(raw["strengthBits"], where), raw["strengthSource"],
                   raw["minSdk"], raw["minSdkSource"])


def _number_problems(row: TypeRow) -> list[str]:
    bad = lambda v: v is not None and (not isinstance(v, int) or v < 1)
    found = [f"outputBytes {row.properties.outputBytes!r} is neither a positive integer nor null"] * bad(row.properties.outputBytes)
    return found + [f"minSdk {row.minSdk!r} is neither an API level nor null"] * bad(row.minSdk)


def _value_problems(row: TypeRow) -> list[str]:
    p = row.properties
    found = [f"outputKind {row.outputKind!r} is not one of {OUTPUT_KINDS}"] * (row.outputKind not in OUTPUT_KINDS)
    found += [f"nonceRequired {p.nonceRequired!r} is not one of {NONCES}"] * (p.nonceRequired not in NONCES)
    found += [f"{k} is not a boolean" for k in ("authenticated", "deterministic") if not isinstance(getattr(p, k), bool)]
    found += [f"{k} is not a string" for k in ("parameters", "keyType") if not isinstance(getattr(p, k), str)]
    return found + _number_problems(row)


def _source_problems(row: TypeRow, sources: dict, maps: dict) -> list[str]:
    found = [f"{k} {getattr(row, k)!r} is not a listed source" for k in ("strengthSource", "minSdkSource")
             if getattr(row, k) not in sources and not (k == "strengthSource" and getattr(row, k) == UNSOURCED)]
    if row.strengthSource == UNSOURCED and row.strength.known:
        found.append("an unsourced strength must be null")
    if row.strength.key is not None and row.strength.key not in maps:
        found.append(f"strength key {row.strength.key!r} is not a keyStrength map")
    return found


def _problems(row: TypeRow, sources: dict, maps: dict) -> list[str]:
    where = f"{row.family} {row.canonical}"
    return [f"{where}: {x}" for x in _value_problems(row) + _source_problems(row, sources, maps)]


def _rows(doc: dict, sources: dict, maps: dict, known) -> tuple[dict[tuple[str, str], TypeRow], list[str]]:
    rows: dict[tuple[str, str], TypeRow] = {}
    problems: list[str] = []
    for family, block in doc["families"].items():
        if family not in known:
            problems.append(f"{family}: not a family of families.yaml")
        for canonical, raw in block["rows"].items():
            row = _row(family, canonical, {**block.get("defaults", {}), **(raw or {})})
            if (family, fold(canonical)) in rows:
                problems.append(f"{family} {canonical}: listed twice")
            rows[(family, fold(canonical))] = row
            problems += _problems(row, sources, maps)
    return rows, problems


def load(path: Path = CATALOG, families: Families | None = None) -> Types:
    doc = yaml.safe_load(Path(path).read_text())
    TYPES_DOC.check(doc, path)
    sources = doc["sources"]
    maps = {name: {int(k): int(v) for k, v in m["bits"].items()} for name, m in doc["keyStrength"].items()}
    problems = [f"keyStrength {n}: source {m['source']!r} is not listed" for n, m in doc["keyStrength"].items()
                if m["source"] not in sources]
    rows, found = _rows(doc, sources, maps, (families or Families.load()).by_id)
    problems += found
    relied = doc["deterministicRelied"]
    problems += [f"deterministicRelied {k!r} is not an output kind" for k in relied if k not in OUTPUT_KINDS]
    if problems:
        raise TypesError("types_invalid: " + "; ".join(problems))
    return Types(rows, maps, frozenset(relied), sources)


@cache
def types() -> Types:
    return load()
