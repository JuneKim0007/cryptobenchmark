from __future__ import annotations

from .. import paths
from dataclasses import dataclass, field
from pathlib import Path

from ..errors.input_error import InputError
from ..document.document import DocumentKind
from .grouping import provider_of
from .glossary import names_problems

CATALOG = paths.repo().algorithms / paths.NAME_INDEX
SCHEMA_VERSION = 2
NAME_CONFLICT = "name_conflict"
SPELLINGS = "spellings"
OID_PREFIX = "OID."


def fold(name: str) -> str:
    return name.upper()


def same_engine(a: str, b: str, canonical_a: str | None, canonical_b: str | None) -> bool:
    """One provider, one canonical name: two spellings of one implementation; an unknown name is never the same."""
    return provider_of(a) == provider_of(b) and None not in (canonical_a, canonical_b) and fold(canonical_a) == fold(canonical_b)


class NamesError(InputError):
    pass


NAMES_DOC = DocumentKind("names", SCHEMA_VERSION, NamesError)


@dataclass(frozen=True)
class Canonical:
    name: str
    keySize: int | None = None
    known: bool = True

    @property
    def key(self) -> tuple[str, int | None]:
        return fold(self.name), self.keySize


@dataclass(frozen=True)
class Transformation:
    modes: dict[str, str]
    paddings: dict[str, str]
    padding_synonyms: dict[str, dict[str, str]]
    mode_synonyms: dict[str, dict[str, str]]


def _folded(spellings: dict[str, list[str]]) -> dict[str, str]:
    table: dict[str, str] = {}
    for canonical, aliases in spellings.items():
        for spelling in [canonical, *(aliases or [])]:
            if table.setdefault(fold(spelling), canonical) != canonical:
                raise NamesError(f"names_catalog_duplicate: {spelling} is under {table[fold(spelling)]} and {canonical}")
    return table


def _check_links(names: dict[str, dict[str, str]], sized: dict[str, dict[str, "Canonical"]]) -> None:
    """A spelling is sized or named, never both; an OID. spelling names what its bare OID names."""
    both = [f"{t} {s} is sized and named" for t, rows in sized.items() for s in rows if s in names.get(t, {})]
    if both:
        raise NamesError("names_catalog_duplicate: " + "; ".join(both))
    split = []
    for t in sorted(set(names) | set(sized)):
        target = {s: (c, None) for s, c in names.get(t, {}).items()} | {s: (c.name, c.keySize) for s, c in sized.get(t, {}).items()}
        split += [f"{t} {s} is {target[s]}, {s[len(OID_PREFIX):]} is {target[s[len(OID_PREFIX):]]}"
                  for s in target if s.startswith(OID_PREFIX) and target.get(s[len(OID_PREFIX):], target[s]) != target[s]]
    if split:
        raise NamesError("names_oid_split: " + "; ".join(split))


def _synonyms(table: dict[str, dict[str, str]]) -> dict[str, dict[str, str]]:
    return {fold(alg): {fold(k): v for k, v in pairs.items()} for alg, pairs in (table or {}).items()}


@dataclass(frozen=True)
class Names:
    names: dict[str, dict[str, str]]
    sized: dict[str, dict[str, Canonical]]
    transformations: dict[str, Transformation]
    key_formats: dict[str, str]
    key_types: dict[str, str] = field(default_factory=dict)
    probe: dict[tuple[str, str], Canonical] = field(default_factory=dict)
    conflicts: dict[tuple[str, str], str] = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path = CATALOG) -> "Names":
        doc = NAMES_DOC.read(path, "names_schema")
        problems = names_problems(doc) + ([] if isinstance(doc.get(SPELLINGS), dict) else [f"no {SPELLINGS}: section"])
        if problems:
            raise NamesError(f"names_schema: {path}: " + "; ".join(problems))
        names = {t: _folded(spellings) for t, spellings in doc[SPELLINGS].items()}
        sized = {t: {fold(s): Canonical(v["name"], v["keySize"]) for s, v in rows.items()} for t, rows in (doc.get("sized") or {}).items()}
        _check_links(names, sized)
        return cls(
            names=names,
            sized=sized,
            transformations={t: Transformation(_folded({m: [] for m in v["modes"]}),
                                               _folded({p: [] for p in v["paddings"]}),
                                               _synonyms(v.get("paddingSynonyms")), _synonyms(v.get("modeSynonyms")))
                             for t, v in (doc.get("transformations") or {}).items()},
            key_formats=_folded({f: [] for f in doc.get("keyFormats") or []}),
            key_types=_folded(doc.get("keyTypes") or {}))

    @property
    def engine_types(self) -> set[str]:
        return set(self.names) | set(self.sized) | set(self.transformations)

    def catalogued(self, engine_type: str, name: str) -> Canonical:
        single = self._single(engine_type, name)
        if single.known or engine_type not in self.transformations or "/" not in name:
            return single
        return self._transformation(engine_type, name)

    def canonical(self, engine_type: str, name: str) -> Canonical:
        """The catalog's name wins over any device alias; only an uncatalogued name the providers disagree on conflicts."""
        found = self.catalogued(engine_type, name)
        if found.known:
            return found
        conflict = self.conflicts.get((engine_type, fold(name)))
        if conflict is not None:
            raise NamesError(f"{NAME_CONFLICT}: {engine_type} {name}: {conflict}")
        return self.probe.get((engine_type, fold(name)), found)

    def key_or_spelling(self, engine_type: str, name: str) -> tuple[str, int | None]:
        """A name_conflict keys by its own spelling: an item to ask, never a stop."""
        try:
            return self.canonical(engine_type, name).key
        except NamesError:
            return fold(name), None

    def key_format(self, name: str) -> Canonical:
        hit = self.key_formats.get(fold(name))
        return Canonical(hit) if hit else Canonical(name, None, False)

    def key_type(self, name: str) -> Canonical:
        """The key type a Key.getAlgorithm() spelling or a catalogue key.type names."""
        hit = self.key_types.get(fold(name))
        return Canonical(hit) if hit else Canonical(name, None, False)

    def _single(self, engine_type: str, name: str) -> Canonical:
        sized = self.sized.get(engine_type, {}).get(fold(name))
        if sized is not None:
            return sized
        hit = self.names.get(engine_type, {}).get(fold(name))
        return Canonical(hit) if hit else Canonical(name, None, False)

    def _transformation(self, engine_type: str, name: str) -> Canonical:
        parts = name.split("/", 2)
        if len(parts) != 3:
            return Canonical(name, None, False)
        base, t = self._single(engine_type, parts[0]), self.transformations[engine_type]
        alg = fold(base.name)
        mode = t.mode_synonyms.get(alg, {}).get(fold(parts[1])) or t.modes.get(fold(parts[1]))
        padding = t.padding_synonyms.get(alg, {}).get(fold(parts[2])) or t.paddings.get(fold(parts[2]))
        # a base that is itself a whole transformation (ELGAMAL -> ELGAMAL/NONE/NoPadding) composes nothing
        if not base.known or "/" in base.name or mode is None or padding is None:
            return Canonical(name, None, False)
        return Canonical(f"{base.name}/{mode}/{padding}", base.keySize)
