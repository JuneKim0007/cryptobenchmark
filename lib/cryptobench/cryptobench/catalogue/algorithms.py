"""catalog/algorithms/: one catalogue per family plus common.yaml, recipes.yaml and deviations.yaml, read and checked whole; an entry's `providers` holds every build's differences once read; entries looked up by family and id."""
from __future__ import annotations

from .paths import DATA
from dataclasses import dataclass
from functools import cache
from pathlib import Path

from ..coded import InputError
from ..document import AT_PATH, DocumentKind
from .types import NO_NONCE, NO_PARAMETERS, OUTPUT_KINDS
from .deviations import CATALOG as DEVIATIONS, Deviations, load as load_deviations
from .families import Families
from .glossary import directions_of, goes_to
from .names import fold
from .overrides import ROW_SECTIONS, override_parent, row_override
from .provider_builds import provider_builds
from .recipes import CATALOG as RECIPES, Recipes, load as load_recipes

DIRECTORY = DATA
COMMON = DIRECTORY / "common.yaml"
SUFFIX = "_catalogue.yaml"
SCHEMA_VERSION = 1
SEPARATOR = "|"
INFERRED, MEASURED, SOURCED = "inferred", "measured", "sourced"
SOURCE_KINDS = (MEASURED, SOURCED, INFERRED)
DETERMINISTIC_VALUES = ("always", "fixedParameters", "never")
ALWAYS = "always"
ENTRY_FIELDS = {"required", "optional", "conditions", "lifecycle", "operations", "sourcedOnly", "providers"}
OPTIONAL_FIELDS = {"key", "contract", "knownVectors"}
CONTRACT_SIDES = ("input", "output")
CLOSED_BOOLEANS = ("passwordBased", "wrap", "prehashed")
CONTRACT_KEY = "key"
KEY_APP, KEY_PROVIDER, KEY_PASSWORD, KEY_NONE = "app", "provider", "password", "none"
KEY_CONTRACTS = (KEY_APP, KEY_PROVIDER, KEY_PASSWORD, KEY_NONE)
VALUE, ASSUMED, RESET = "value", "assumed", "reset"
PROVIDER_SPEC = "providerSpec"
PARAMETER_KIND = {"jca.ivSpec": "iv", "jca.nonceIvSpec": "iv", "jca.gcmSpec": "gcm", "jca.chacha20Spec": "chacha", "jca.pbeSpec": "pbe", "jca.pbeIvSpec": "pbe"}
NONCE_RULES = ("unpredictable", "unique")
OUTPUT, DETERMINISTIC, AUTHENTICATED = "output", "deterministic", "authenticated"
STRENGTH, MIN_SDK = "strengthBits", "minSdk"
NO_OUTPUT_BYTES = ("keygen.none", "keypairgen.none", "agreement.peer")
FIXED = "fixed:"


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

    def _carrying(self) -> list[dict]:
        """The rows that state a parameter object or nonce: the base's, or with no base row each build's own, in PARAMETER_KIND's order so no build count decides."""
        wanted = [r for r in self.raw["required"] if r.get("recipe") in PARAMETER_KIND or "rule" in r]
        builds = [v for _, over in sorted(self.raw["providers"].items()) for k, v in sorted(over.items())
                  if row_override(k) and isinstance(v, dict) and (v.get("recipe") in PARAMETER_KIND or "rule" in v)]
        return wanted or sorted(builds, key=lambda r: list(PARAMETER_KIND).index(r["recipe"]) if r.get("recipe") in PARAMETER_KIND else len(PARAMETER_KIND))

    @property
    def parameters(self) -> str:
        """The shape of the parameter object the call passes, by the recipe a row names; none without one."""
        return next((PARAMETER_KIND[r["recipe"]] for r in self._carrying() if r.get("recipe") in PARAMETER_KIND), NO_PARAMETERS)

    @property
    def nonce(self) -> str:
        """How the IV or nonce must be chosen; none without one."""
        return next((r["rule"] for r in self._carrying() if "rule" in r), NO_NONCE)


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


def lifecycle_leaves(raw: dict) -> list[tuple[str, dict]]:
    """(override path, leaf) of each lifecycle fact: reset holds one leaf per direction."""
    found: list[tuple[str, dict]] = []
    for name, row in raw["lifecycle"].items():
        found += [(f"lifecycle.{name}.{side}", leaf) for side, leaf in row.items()] if name == RESET else [(f"lifecycle.{name}", row)]
    return found


def _reset_problems(raw: dict) -> list[str]:
    """Reset holds exactly the directions the entry's operations run in."""
    held, wanted = set(raw["lifecycle"].get(RESET) or {}), directions_of(raw["operations"].get(VALUE))
    return [f"{RESET} holds {sorted(held)}, the operations run {sorted(wanted)}"] * (held != wanted)


def _source_problems(value: dict) -> list[str]:
    source = value.get("source") if isinstance(value, dict) else None
    if source not in SOURCE_KINDS:
        return [f"source {source!r} is not one of {SOURCE_KINDS}"]
    return [f"a sourced value has no url: {value}"] * (source == SOURCED and not value.get("url"))


def _strength_problems(raw, key_strength: dict) -> list[str]:
    if raw is None or type(raw) is int:
        return []
    if isinstance(raw, dict) and set(raw) <= {"key", "cap"} and "key" in raw:
        return [f"strength key {raw['key']!r} is not a keyStrength map"] * (raw["key"] not in key_strength)
    return [f"strengthBits {raw!r} is neither bits, {{key, cap}} nor null"]


def _type_fact_problems(entry: Entry) -> list[str]:
    """The type facts come whole or not at all: key, output, determinism, authentication, strength, minSdk."""
    raw, conditions = entry.raw, entry.raw["conditions"]
    carried = {path.split(".")[1] for over in raw["providers"].values() if isinstance(over, dict) for path in over if path.startswith("conditions.")}
    present = {"key": "key" in raw,
               **{k: k in conditions or k in carried for k in (OUTPUT, DETERMINISTIC, AUTHENTICATED)},
               STRENGTH: entry.sourced(STRENGTH) is not None, MIN_SDK: entry.sourced(MIN_SDK) is not None}
    if not any(present.values()):
        return []
    if not all(present.values()):
        return [f"type facts missing {sorted(k for k, v in present.items() if not v)}"]
    found = [f"key type {raw['key'].get('type')!r} is not a string"] * (not isinstance(raw["key"].get("type"), str))
    found += [f"nonce rule {r['rule']!r} is not one of {NONCE_RULES}" for r in raw["required"] if "rule" in r and r["rule"] not in NONCE_RULES]
    output = conditions[OUTPUT]
    found += [f"output kind {output.get('kind')!r} is not one of {OUTPUT_KINDS}"] * (output.get("kind") not in OUTPUT_KINDS)
    found += [f"output bytes {output.get('bytes')!r} is neither a positive integer nor null"] * _not_positive(output.get("bytes"))
    deterministic, authenticated = (conditions.get(k, {}).get(VALUE, DETERMINISTIC_VALUES[0]) for k in (DETERMINISTIC, AUTHENTICATED))
    found += [f"deterministic {deterministic!r} is not one of {DETERMINISTIC_VALUES}"] * (deterministic not in DETERMINISTIC_VALUES)
    found += [f"{AUTHENTICATED} is not a boolean"] * (AUTHENTICATED in conditions and not isinstance(authenticated, bool))
    return found + [f"minSdk {entry.sourced(MIN_SDK).get('value')!r} is neither an API level nor null"] \
        * _not_positive(entry.sourced(MIN_SDK).get("value"))


def _output_problems(entry: Entry) -> list[str]:
    """A generator or an agreement has no result length to state; a stated length is what the formula fixes."""
    output = entry.raw["conditions"].get(OUTPUT)
    if not isinstance(output, dict) or output.get("bytes") is None:
        return []
    size, formula = output["bytes"], output.get("formula")
    found = [f"output bytes {size!r}: family {entry.family} states no result length"] * (entry.family in NO_OUTPUT_BYTES)
    return found + [f"output bytes {size!r} is not what formula {formula!r} fixes"] * (formula is not None and formula != f"{FIXED}{size}")


def _passed_to_problems(entry: Entry) -> list[str]:
    """Each required row, base and build, names a call its role may go to on this engine type."""
    raw = entry.raw
    rows = [*raw["required"], *(v for o in raw["providers"].values() if isinstance(o, dict) for k, v in o.items()
                                 if row_override(k) and row_override(k)[0] == ROW_SECTIONS[0] and isinstance(v, dict))]
    found = []
    for row in rows:
        allowed = goes_to(row.get("name"), entry.type)
        if allowed is not None and row.get("passedTo") not in allowed:
            found.append(f"required {row.get('name')!r}: passedTo {row.get('passedTo')!r} on {entry.type} is none of {allowed}")
    return [*dict.fromkeys(found)]


def _not_positive(value) -> bool:
    return value is not None and (type(value) is not int or value < 1)


def _leaf_problems(entry: Entry, common: Common) -> list[str]:
    raw, found = entry.raw, []
    leaves = [*([raw["key"]] if "key" in raw else []), *raw["required"], *raw["optional"], *raw["conditions"].values(),
              *(leaf for _, leaf in lifecycle_leaves(raw)), raw["operations"], *raw["sourcedOnly"]]
    for leaf in leaves:
        found += _source_problems(leaf)
    strength = entry.sourced(STRENGTH)
    if strength is not None:
        found += _strength_problems(strength.get("value"), common.key_strength)
    return found


def _contract_problems(contract) -> list[str]:
    if contract is None:
        return []
    if not isinstance(contract, dict) or set(contract) != {*CONTRACT_SIDES, CONTRACT_KEY}:
        return [f"contract {contract!r} is not {{key, input, output}}"]
    found = [f"contract key {contract[CONTRACT_KEY]!r} is not one of {KEY_CONTRACTS}"] * (contract[CONTRACT_KEY] not in KEY_CONTRACTS)
    found += [f"contract {side} is not a mapping of plain values or {{{VALUE}, {ASSUMED}: true}}" for side in CONTRACT_SIDES
              if not isinstance(contract[side], dict) or not all(map(_contract_value_form, contract[side].values()))]
    return found + [f"contract {side}.{k} {v!r} is not a boolean" for side in CONTRACT_SIDES if isinstance(contract[side], dict)
                    for k, v in contract[side].items() if k in CLOSED_BOOLEANS and type(v) is not bool]


def _contract_value_form(value) -> bool:
    return isinstance(value, (str, bool, int)) or (isinstance(value, dict) and set(value) == {VALUE, ASSUMED}
                                                   and isinstance(value[VALUE], str) and value[ASSUMED] is True)


def contract_value(value) -> str:
    return value[VALUE] if isinstance(value, dict) else value


def contract_assumed(value) -> bool:
    return isinstance(value, dict) and value[ASSUMED]


def _shape_problems(raw) -> list[str]:
    if not isinstance(raw, dict):
        return ["an entry is not a mapping"]
    missing, stray = ENTRY_FIELDS - set(raw), set(raw) - ENTRY_FIELDS - OPTIONAL_FIELDS
    if missing or stray:
        return [f"fields missing {sorted(missing)}, unknown {sorted(stray)}"]
    kinds = {"required": list, "optional": list, "sourcedOnly": list, "conditions": dict, "lifecycle": dict, "operations": dict,
             "providers": dict}
    found = [f"{k} is not a {t.__name__}" for k, t in kinds.items() if not isinstance(raw[k], t)]
    found += [f"{k} holds a non-mapping" for k in ("required", "optional", "sourcedOnly")
              if isinstance(raw[k], list) and not all(isinstance(x, dict) for x in raw[k])]
    return found + [f"{k} holds a non-mapping" for k in ("conditions", "lifecycle")
                    if isinstance(raw[k], dict) and not all(isinstance(v, dict) for v in raw[k].values())]


def _override_problem(raw: dict, path: str, value) -> bool:
    row = row_override(path)
    if row is None:
        return override_parent(raw, path) is None
    if value is None:
        return False
    return not isinstance(value, dict) or value.get("name") != row[1]


def _provider_problems(raw: dict, builds: dict | None = None) -> list[str]:
    found = [f"provider {p!r} override {path!r} names no field of the entry" for p, overrides in raw["providers"].items()
             for path, value in (overrides if isinstance(overrides, dict) else {"": None}).items() if _override_problem(raw, path, value)]
    return found + [f"provider {p!r} is no build of provider-builds.yaml" for p in raw["providers"] if builds is not None and p not in builds]


def _recipe_problems(raw: dict, recipes: Recipes) -> list[str]:
    """A row's recipe exists and passes the row's role, unless a builder makes it or the row is the object itself; one call takes one object and one object goes to one call, base and build alike."""
    rows = [*raw["required"], *(v for o in raw["providers"].values() if isinstance(o, dict) for k, v in o.items()
                                 if row_override(k) and isinstance(v, dict))]
    found = []
    for row in rows:
        recipe = row.get("recipe")
        if recipe is None:
            continue
        if recipe not in recipes.by_id:
            found.append(f"required {row.get('name')!r}: recipe {recipe!r} is no recipe of recipes.yaml")
        elif not recipes.built_by_hand(recipe) and row.get("name") not in recipes.roles(recipe) | {PROVIDER_SPEC}:
            found.append(f"required {row.get('name')!r}: recipe {recipe} passes no such role")
    return found + _one_object_problems(raw)


def _one_object_problems(raw: dict) -> list[str]:
    found = []
    for build, over in [(None, {}), *((b, o) for b, o in raw["providers"].items() if isinstance(o, dict))]:
        seen = {r.get("name"): r for r in raw["required"]}
        for path, value in over.items():
            if row_override(path) and row_override(path)[0] == ROW_SECTIONS[0]:
                seen[row_override(path)[1]] = value
        calls: dict[str, set[str]] = {}
        goes: dict[str, set[str]] = {}
        for row in seen.values():
            if isinstance(row, dict) and row.get("recipe"):
                calls.setdefault(row.get("passedTo"), set()).add(row["recipe"])
                goes.setdefault(row["recipe"], set()).add(str(row.get("passedTo")))
        at = f" @ {build}" if build else ""
        found += [f"{call} takes one object, the rows name {sorted(held)}{at}" for call, held in calls.items() if len(held) > 1]
        found += [f"recipe {recipe} is one object, the rows pass it to {sorted(to)}{at}" for recipe, to in goes.items() if len(to) > 1]
    return found


def entry_problems(entry: Entry, common: Common, builds: dict | None = None, recipes: Recipes | None = None) -> list[str]:
    """One entry's form: its fields, the id's two parts, each leaf's source, the contract, type facts and overrides."""
    found = _shape_problems(entry.raw)
    if found:
        return found
    found = [f"id {entry.id!r} is not <type>{SEPARATOR}<canonical>"] * (split_id(entry.id) is None)
    return found + _leaf_problems(entry, common) + _reset_problems(entry.raw) + _output_problems(entry) + _passed_to_problems(entry) + _contract_problems(entry.raw.get("contract")) + _type_fact_problems(entry) \
        + _provider_problems(entry.raw, builds) + (_recipe_problems(entry.raw, recipes) if recipes is not None else [])


def _common(path: Path) -> tuple[Common, list[str]]:
    doc = CATALOGUE_DOC.read(path, INVALID)
    sources = doc["sources"]
    maps = {name: {int(k): int(v) for k, v in m["bits"].items()} for name, m in doc["keyStrength"].items()}
    problems = [f"keyStrength {n}: source {m['source']!r} is not listed" for n, m in doc["keyStrength"].items()
                if m["source"] not in sources]
    relied = doc["deterministicRelied"]
    problems += [f"deterministicRelied {k!r} is not an output kind" for k in relied if k not in OUTPUT_KINDS]
    return Common(sources, maps, frozenset(relied)), problems


def _catalogue(path: Path, family: str, common: Common, recipes: Recipes, deviations: Deviations) -> tuple[list[Entry], list[str]]:
    doc = CATALOGUE_DOC.read(path, INVALID)
    if doc.get("family") != family or not isinstance(doc.get("algorithms"), dict):
        return [], [f"{path.name}: family {doc.get('family')!r} is not {family}, or algorithms is not a mapping"]
    entries = [Entry(i, family, deviations.overlaid(i, raw)) for i, raw in doc["algorithms"].items()]
    builds = provider_builds().builds
    problems = [f"{family} {e.id}: {p}" for e in entries for p in entry_problems(e, common, builds, recipes)]
    seen: set[str] = set()
    for e in entries:
        problems += [f"{family} {e.id}: listed twice"] * (fold(e.id) in seen)
        seen.add(fold(e.id))
    return entries, problems


def load(directory: Path = DIRECTORY, families: Families | None = None) -> Algorithms:
    directory = Path(directory)
    common, problems = _common(directory / COMMON.name)
    recipes = load_recipes(directory / RECIPES.name)
    deviations = load_deviations(directory / DEVIATIONS.name, provider_builds())
    known = {f.id for f in (families or Families.load()).all}
    files = {p.name[:-len(SUFFIX)]: p for p in sorted(directory.glob("*" + SUFFIX))}
    problems += [f"{f}{SUFFIX}: not a family of families.yaml" for f in files if f not in known]
    problems += [f"{f}: no {f}{SUFFIX}" for f in known if f not in files]
    entries: list[Entry] = []
    for family in (f for f in known if f in files):
        found, more = _catalogue(files[family], family, common, recipes, deviations)
        entries += found
        problems += more
    problems += deviations.problems({fold(e.id) for e in entries})
    if problems:
        raise AlgorithmsError(f"{INVALID}: " + "; ".join(problems))
    return Algorithms(tuple(entries), common)


@cache
def algorithms() -> Algorithms:
    return load()
