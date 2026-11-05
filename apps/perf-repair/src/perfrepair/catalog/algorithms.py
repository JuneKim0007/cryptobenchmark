"""catalog/algorithms/: one catalogue per family plus common.yaml, read and checked whole; entries looked up by family and id."""
from __future__ import annotations

from dataclasses import dataclass
from functools import cache
from pathlib import Path

from ..dto.coded import InputError
from ..dto.document import AT_PATH, DocumentKind
from ..dto.types import NONCES, OUTPUT_KINDS
from .families import Families
from .names import fold

DIRECTORY = Path(__file__).with_name("algorithms")
COMMON = DIRECTORY / "common.yaml"
SUFFIX = "_catalogue.yaml"
SCHEMA_VERSION = 1
SEPARATOR = "|"
UNSOURCED, INFERRED, MEASURED = "unsourced", "inferred", "measured"
PERSON, AGENT = "person", "agent"
ENTRY_FIELDS = {"required", "optional", "conditions", "sourcedOnly", "providers", "provenance"}
OPTIONAL_FIELDS = {"aliases", "key", "contract"}
CONTRACT_SIDES = ("input", "output")
PARAMETERS, NONCE = "parameters", "nonce"
OUTPUT, DETERMINISTIC, AUTHENTICATED = "output", "deterministic", "authenticated"
STRENGTH, MIN_SDK = "strengthBits", "minSdk"


class AlgorithmsError(InputError):
    pass


INVALID = "algorithms_invalid"
CATALOGUE_DOC = DocumentKind("algorithms", SCHEMA_VERSION, INVALID + ": " + AT_PATH, AlgorithmsError)


@dataclass(frozen=True)
class Entry:
    id: str
    family: str
    raw: dict

    @property
    def type(self) -> str:
        return self.id.split(SEPARATOR, 1)[0]

    @property
    def canonical(self) -> str:
        return self.id.split(SEPARATOR, 1)[1]

    @property
    def contract(self) -> dict | None:
        return self.raw.get("contract")

    def required(self, name: str) -> dict | None:
        return next((r for r in self.raw["required"] if r.get("name") == name), None)

    def sourced(self, fact: str) -> dict | None:
        return next((s for s in self.raw["sourcedOnly"] if s.get("fact") == fact), None)


@dataclass(frozen=True)
class Common:
    sources: dict[str, str]
    key_strength: dict[str, dict[int, int]]
    deterministic_relied: frozenset[str]


@dataclass(frozen=True)
class Algorithms:
    entries: tuple[Entry, ...]
    common: Common

    def __post_init__(self):
        object.__setattr__(self, "_by_key", {(e.family, fold(e.id)): e for e in self.entries})

    def of(self, family: str, algorithm_id: str) -> Entry | None:
        return self._by_key.get((family, fold(algorithm_id)))

    def family(self, family: str) -> list[Entry]:
        return [e for e in self.entries if e.family == family]


def algorithm_id(engine_type: str, canonical: str) -> str:
    return f"{engine_type}{SEPARATOR}{canonical}"


def split_id(value: object) -> tuple[str, str] | None:
    """None: not `<type>|<canonical>` with both parts."""
    if not isinstance(value, str) or value.count(SEPARATOR) != 1:
        return None
    engine_type, canonical = value.split(SEPARATOR)
    return (engine_type, canonical) if engine_type and canonical else None


def _source_problems(value: dict, sources: dict, allowed: tuple[str, ...]) -> list[str]:
    source = value.get("source") if isinstance(value, dict) else None
    return [] if source in sources or source in allowed else [f"source {source!r} is not a listed source or one of {allowed}"]


def _strength_problems(raw, source: str, key_strength: dict) -> list[str]:
    if raw is None or type(raw) is int:
        found = []
    elif isinstance(raw, dict) and set(raw) <= {"key", "cap"} and "key" in raw:
        found = [f"strength key {raw['key']!r} is not a keyStrength map"] * (raw["key"] not in key_strength)
    else:
        return [f"strengthBits {raw!r} is neither bits, {{key, cap}} nor null"]
    return found + ["an unsourced strength must be null"] * (source == UNSOURCED and raw is not None)


def _type_fact_problems(entry: Entry) -> list[str]:
    """The type facts come whole or not at all: key, parameters, nonce, output, determinism, authentication, strength, minSdk."""
    raw, conditions = entry.raw, entry.raw["conditions"]
    parameters, nonce = entry.required(PARAMETERS), entry.required(NONCE)
    present = {"key": "key" in raw, PARAMETERS: parameters is not None, NONCE: nonce is not None,
               **{k: k in conditions for k in (OUTPUT, DETERMINISTIC, AUTHENTICATED)},
               STRENGTH: entry.sourced(STRENGTH) is not None, MIN_SDK: entry.sourced(MIN_SDK) is not None}
    if not any(present.values()):
        return []
    if not all(present.values()):
        return [f"type facts missing {sorted(k for k, v in present.items() if not v)}"]
    found = [f"key type {raw['key'].get('type')!r} is not a string"] * (not isinstance(raw["key"].get("type"), str))
    found += [f"parameters {parameters.get('value')!r} is not a string"] * (not isinstance(parameters.get("value"), str))
    found += [f"nonce {nonce.get('value')!r} is not one of {NONCES}"] * (nonce.get("value") not in NONCES)
    output = conditions[OUTPUT]
    found += [f"output kind {output.get('kind')!r} is not one of {OUTPUT_KINDS}"] * (output.get("kind") not in OUTPUT_KINDS)
    found += [f"output bytes {output.get('bytes')!r} is neither a positive integer nor null"] * _not_positive(output.get("bytes"))
    found += [f"{k} is not a boolean" for k in (DETERMINISTIC, AUTHENTICATED) if not isinstance(conditions[k].get("value"), bool)]
    return found + [f"minSdk {entry.sourced(MIN_SDK).get('value')!r} is neither an API level nor null"] \
        * _not_positive(entry.sourced(MIN_SDK).get("value"))


def _not_positive(value) -> bool:
    return value is not None and (type(value) is not int or value < 1)


def _leaf_problems(entry: Entry, common: Common) -> list[str]:
    raw, sources, found = entry.raw, common.sources, []
    leaves = [*([raw["key"]] if "key" in raw else []), *raw["required"], *raw["optional"], *raw["conditions"].values()]
    for leaf in leaves:
        found += _source_problems(leaf, sources, (MEASURED, INFERRED))
    for fact in raw["sourcedOnly"]:
        found += _source_problems(fact, sources, (UNSOURCED,) if fact.get("fact") != MIN_SDK else ())
    strength = entry.sourced(STRENGTH)
    if strength is not None:
        found += _strength_problems(strength.get("value"), strength.get("source"), common.key_strength)
    return found


def _contract_problems(contract) -> list[str]:
    if contract is None:
        return []
    if not isinstance(contract, dict) or set(contract) != set(CONTRACT_SIDES):
        return [f"contract {contract!r} is not {{input, output}}"]
    return [f"contract {side} is not a mapping of strings" for side in CONTRACT_SIDES
            if not isinstance(contract[side], dict) or not all(isinstance(v, str) for v in contract[side].values())]


def _shape_problems(raw) -> list[str]:
    if not isinstance(raw, dict):
        return ["an entry is not a mapping"]
    missing, stray = ENTRY_FIELDS - set(raw), set(raw) - ENTRY_FIELDS - OPTIONAL_FIELDS
    if missing or stray:
        return [f"fields missing {sorted(missing)}, unknown {sorted(stray)}"]
    kinds = {"required": list, "optional": list, "sourcedOnly": list, "conditions": dict, "providers": dict, "provenance": dict}
    found = [f"{k} is not a {t.__name__}" for k, t in kinds.items() if not isinstance(raw[k], t)]
    found += [f"{k} holds a non-mapping" for k in ("required", "optional", "sourcedOnly")
              if isinstance(raw[k], list) and not all(isinstance(x, dict) for x in raw[k])]
    return found + ["conditions holds a non-mapping"] * (isinstance(raw["conditions"], dict)
                                                          and not all(isinstance(v, dict) for v in raw["conditions"].values()))


def override_parent(base: dict, path: str) -> tuple[dict, str] | None:
    """A provider override `a.b.c`: the mapping that holds c; a list step picks the item named, or the fact, b."""
    *steps, last = path.split(".")
    node = base
    for step in steps:
        if isinstance(node, dict):
            node = node.get(step)
        elif isinstance(node, list):
            node = next((x for x in node if isinstance(x, dict) and step in (x.get("name"), x.get("fact"))), None)
        else:
            return None
    return (node, last) if isinstance(node, dict) and last and steps and steps[0] != "providers" else None


def _provider_problems(raw: dict) -> list[str]:
    return [f"provider {p!r} override {path!r} names no field of the entry" for p, overrides in raw["providers"].items()
            for path in (overrides if isinstance(overrides, dict) else {"": None}) if override_parent(raw, path) is None]


def entry_problems(entry: Entry, common: Common) -> list[str]:
    """One entry's form: its fields, the id's two parts, each leaf's provenance, the contract, type facts and overrides."""
    found = _shape_problems(entry.raw)
    if found:
        return found
    by = entry.raw["provenance"].get("by")
    found = [f"id {entry.id!r} is not <type>{SEPARATOR}<canonical>"] * (split_id(entry.id) is None)
    found += [f"provenance by {by!r} is neither {PERSON} nor {AGENT}"] * (by not in (PERSON, AGENT))
    return found + _leaf_problems(entry, common) + _contract_problems(entry.raw.get("contract")) + _type_fact_problems(entry) \
        + _provider_problems(entry.raw)


def _common(path: Path) -> tuple[Common, list[str]]:
    doc = CATALOGUE_DOC.read(path, INVALID)
    sources = doc["sources"]
    maps = {name: {int(k): int(v) for k, v in m["bits"].items()} for name, m in doc["keyStrength"].items()}
    problems = [f"keyStrength {n}: source {m['source']!r} is not listed" for n, m in doc["keyStrength"].items()
                if m["source"] not in sources]
    relied = doc["deterministicRelied"]
    problems += [f"deterministicRelied {k!r} is not an output kind" for k in relied if k not in OUTPUT_KINDS]
    return Common(sources, maps, frozenset(relied)), problems


def _catalogue(path: Path, family: str, common: Common) -> tuple[list[Entry], list[str]]:
    doc = CATALOGUE_DOC.read(path, INVALID)
    if doc.get("family") != family or not isinstance(doc.get("algorithms"), dict):
        return [], [f"{path.name}: family {doc.get('family')!r} is not {family}, or algorithms is not a mapping"]
    entries = [Entry(i, family, raw) for i, raw in doc["algorithms"].items()]
    problems = [f"{family} {e.id}: {p}" for e in entries for p in entry_problems(e, common)]
    seen: set[str] = set()
    for e in entries:
        problems += [f"{family} {e.id}: listed twice"] * (fold(e.id) in seen)
        seen.add(fold(e.id))
    return entries, problems


def load(directory: Path = DIRECTORY, families: Families | None = None) -> Algorithms:
    directory = Path(directory)
    common, problems = _common(directory / COMMON.name)
    known = (families or Families.load()).by_id
    files = {p.name[:-len(SUFFIX)]: p for p in sorted(directory.glob("*" + SUFFIX))}
    problems += [f"{f}{SUFFIX}: not a family of families.yaml" for f in files if f not in known]
    problems += [f"{f}: no {f}{SUFFIX}" for f in known if f not in files]
    entries: list[Entry] = []
    for family in (f for f in known if f in files):
        found, more = _catalogue(files[family], family, common)
        entries += found
        problems += more
    if problems:
        raise AlgorithmsError(f"{INVALID}: " + "; ".join(problems))
    return Algorithms(tuple(entries), common)


@cache
def algorithms() -> Algorithms:
    return load()
