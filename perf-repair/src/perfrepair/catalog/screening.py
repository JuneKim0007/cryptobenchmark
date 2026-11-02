from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from .names import Names, fold

SCREENING = Path(__file__).with_name("screening.yaml")
SCHEMA_VERSION = 1
DEPRECATED, ACCEPTED = "deprecated", "accepted"
STATUSES = (DEPRECATED, ACCEPTED)
GATES = ("targetSdk",)
UNSOURCED = "unsourced"


class ScreeningError(ValueError):
    pass


@dataclass(frozen=True)
class Rule:
    status: str
    reason: str
    source: str


@dataclass(frozen=True)
class PlatformRule:
    deprecatedApi: int
    removedApi: int | None
    gate: str
    reason: str
    source: str


@dataclass(frozen=True)
class Note:
    note: str
    source: str


@dataclass(frozen=True)
class Components:
    bases: dict[str, Rule]
    modes: dict[str, Rule]


@dataclass(frozen=True)
class Screening:
    crypto: dict[tuple[str, str], Rule]
    components: dict[str, Components]
    platform: dict[tuple[str, str, str], PlatformRule]
    future: dict[tuple[str, str], Note]

    @classmethod
    def load(cls, path: Path = SCREENING, names: Names | None = None) -> "Screening":
        return _Reader(yaml.safe_load(Path(path).read_text()), names or Names.load(), Path(path)).screening()

    def component(self, engine_type: str, canonical: str, names: Names) -> Rule | None:
        rules = self.components.get(engine_type)
        if rules is None:
            return None
        parts = [fold(p) for p in canonical.split("/")]
        if parts[0] in rules.bases:
            return rules.bases[parts[0]]
        if len(parts) != 3 or parts[1] not in rules.modes:
            return None
        synonyms = names.transformations[engine_type].mode_synonyms.get(parts[0], {})
        # a mode the catalog maps another mode onto for this base is nominal there, never a chaining mode
        return None if parts[1] in {fold(m) for m in synonyms.values()} else rules.modes[parts[1]]


class _Reader:

    def __init__(self, doc: dict, names: Names, path: Path):
        self.doc, self.names, self.path, self.problems = doc or {}, names, path, []

    def screening(self) -> Screening:
        if self.doc.get("schemaVersion") != SCHEMA_VERSION:
            raise ScreeningError(f"screening_schema: {self.path}: schemaVersion {self.doc.get('schemaVersion')} "
                                 f"is not {SCHEMA_VERSION}")
        self.sources = self.doc.get("sources") or {}
        built = Screening(self._crypto(), self._components(), self._platform(), self._future())
        self._contradictions(built)
        if self.problems:
            raise ScreeningError("; ".join(self.problems))
        return built

    def _source(self, where: str, key) -> str:
        if key == UNSOURCED:
            return UNSOURCED
        if key not in self.sources:
            self.problems.append(f"screening_source: {where}: {key!r} is not in sources")
        return self.sources.get(key, str(key))

    def _rule(self, where: str, raw: dict) -> Rule:
        if raw.get("status") not in STATUSES:
            self.problems.append(f"screening_status: {where}: {raw.get('status')!r} is not one of {list(STATUSES)}")
        if not raw.get("reason"):
            self.problems.append(f"screening_reason: {where}: no reason")
        return Rule(raw.get("status"), raw.get("reason") or "", self._source(where, raw.get("source")))

    def _key(self, where: str, engine_type: str, name: str) -> tuple[str, str]:
        found = self.names.catalogued(engine_type, str(name))
        if not found.known or found.keySize is not None or found.name != name:
            said = f"canonical is {found.name}" if found.known else "not in algorithm-names.yaml"
            self.problems.append(f"screening_key_not_canonical: {where} {engine_type} {name}: {said}")
        return engine_type, fold(str(name))

    def _crypto(self) -> dict[tuple[str, str], Rule]:
        return {self._key("crypto", t, n): self._rule(f"crypto {t} {n}", raw)
                for t, rows in (self.doc.get("crypto") or {}).items() for n, raw in rows.items()}

    def _future(self) -> dict[tuple[str, str], Note]:
        return {self._key("future", t, n): Note(raw.get("note") or "", self._source(f"future {t} {n}", raw.get("source")))
                for t, rows in (self.doc.get("future") or {}).items() for n, raw in rows.items()}

    def _components(self) -> dict[str, Components]:
        out = {}
        for t, raw in (self.doc.get("components") or {}).items():
            transformation = self.names.transformations.get(t)
            if transformation is None:
                self.problems.append(f"screening_component_type: {t} has no transformations in algorithm-names.yaml")
                continue
            bases = {self._key("components base", t, b)[1]: self._component(f"{t} base {b}", r)
                     for b, r in (raw.get("base") or {}).items()}
            modes = {}
            for m, r in (raw.get("mode") or {}).items():
                if transformation.modes.get(fold(m)) != m:
                    self.problems.append(f"screening_key_not_canonical: components mode {t} {m}: not a catalog mode")
                modes[fold(m)] = self._component(f"{t} mode {m}", r)
            out[t] = Components(bases, modes)
        return out

    def _component(self, where: str, raw: dict) -> Rule:
        rule = self._rule(f"components {where}", raw)
        if rule.status != DEPRECATED:
            self.problems.append(f"screening_component_status: {where}: a component rule only deprecates")
        return rule

    def _platform(self) -> dict[tuple[str, str, str], PlatformRule]:
        out: dict[tuple[str, str, str], PlatformRule] = {}
        for n, raw in enumerate(self.doc.get("platform") or []):
            where = f"platform[{n}] {raw.get('provider')}"
            rule = self._platform_rule(where, raw)
            for t, listed in (raw.get("names") or {}).items():
                for name in listed:
                    key = (raw.get("provider"), *self._key(where, t, name))
                    if key in out:
                        self.problems.append(f"screening_duplicate: {where} {t} {name} is listed twice")
                    out[key] = rule
        return out

    def _platform_rule(self, where: str, raw: dict) -> PlatformRule:
        deprecated, removed = raw.get("deprecatedApi"), raw.get("removedApi")
        if not raw.get("provider"):
            self.problems.append(f"screening_platform: {where}: no provider")
        if raw.get("gate") not in GATES:
            self.problems.append(f"screening_gate: {where}: {raw.get('gate')!r} is not one of {list(GATES)}")
        if not isinstance(deprecated, int) or (removed is not None and (not isinstance(removed, int) or removed <= deprecated)):
            self.problems.append(f"screening_platform: {where}: deprecatedApi {deprecated!r}, removedApi {removed!r}")
        return PlatformRule(deprecated, removed, raw.get("gate"), raw.get("reason") or "",
                            self._source(where, raw.get("source")))

    def _contradictions(self, built: Screening) -> None:
        for (t, name), rule in built.crypto.items():
            component = built.component(t, self.names.catalogued(t, name).name, self.names)
            if rule.status == ACCEPTED and component is not None:
                self.problems.append(f"screening_contradiction: crypto {t} {name} is accepted but a component "
                                     f"deprecates it: {component.reason}")
