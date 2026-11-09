"""catalog/glossary.yaml: one meaning per word of the catalogues, recipes.yaml, deviations.yaml and groups.yaml. what_is looks a term up; term_problems checks an entry, recipe_problems the recipes."""
from __future__ import annotations

from .paths import DATA
import re
from functools import cache

from ..coded import InputError
from ..document import AT_PATH, DocumentKind

CATALOG = DATA / "glossary.yaml"
SCHEMA_VERSION = 1
UNKNOWN = "glossary_unknown"
ALGORITHM, GROUP, RECIPE = "algorithm", "group", "recipe"
MEANS, VALUES, FORMAT, NULLABLE, UNUSED, DERIVED = "means", "values", "format", "nullable", "unused", "derived"
MAKE, LIVES, DIRECTIONS, RESET, GOES_TO = "make", "lives", "directions", "reset", "goesTo"
TERM_FIELDS = {MEANS, VALUES, FORMAT, NULLABLE, UNUSED, DERIVED, MAKE, LIVES, DIRECTIONS, GOES_TO}
BUILD, NAMES, DEVIATION = "build", "names", "deviation"
LEAF_ANYWHERE = ("source", "url")
ALL = object()
PROVIDER_KEY = re.compile(r"^\S+ @ \S+$")
ALGORITHM_ID = re.compile(r"^[A-Za-z]+\|.+$")
URL = re.compile(r"^https?://\S+$")
RECIPE_ID = re.compile(r"^[a-z]+\.[A-Za-z0-9]+$")
DEVIATION_ID = RECIPE_ID
OUTPUT_FORMULA = re.compile(r"^(same|any|(pad|plus|fixed):[1-9][0-9]*)$")
CLASS_NAME = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+\.[A-Z][A-Za-z0-9_$]*$")


class GlossaryError(InputError):
    pass


GLOSSARY_DOC = DocumentKind("glossary", SCHEMA_VERSION, UNKNOWN + ": " + AT_PATH, GlossaryError)


@cache
def tree() -> dict:
    return GLOSSARY_DOC.read(CATALOG, UNKNOWN)


def _is_term(node) -> bool:
    return isinstance(node, dict) and MEANS in node


def _children(node: dict) -> list[str]:
    return [str(k) for k in node if k not in TERM_FIELDS]


def _node(path: str):
    node = tree()
    for step in path.split("."):
        if not isinstance(node, dict) or step in TERM_FIELDS or step not in node:
            valid = _children(node) if isinstance(node, dict) else []
            raise GlossaryError(f"{UNKNOWN}: {path}: no term {step!r}; valid here: {valid}")
        node = node[step]
    return node


def roles() -> dict:
    return tree()[ALGORITHM]["role"]


def _operations() -> dict:
    return tree()[ALGORITHM]["operations"]["value"][VALUES]


def direction_of(operation: str) -> str:
    """forward or reverse; an operation the glossary does not list is coded."""
    what_is("algorithm.operations.value", operation)
    return tree()[ALGORITHM]["operations"]["value"][DIRECTIONS][operation]


def goes_to(role: str, engine: str) -> list[str] | None:
    """The calls a required row of the role may name on that engine type; None for a word that is no role."""
    return roles()[role].get(GOES_TO, {}).get(engine, []) if role in roles() else None


def directions_of(operations) -> set[str]:
    """The directions an entry's operations run in; a word the glossary does not list has none."""
    held = tree()[ALGORITHM]["operations"]["value"][DIRECTIONS]
    return {held[op] for op in operations if op in held} if isinstance(operations, list) else set()


def lives(role: str, direction: str) -> str:
    """How long one value of the role is used in that direction."""
    held = roles()[role][LIVES]
    return held[direction] if isinstance(held, dict) else held


def _fits(term: dict, value) -> bool:
    if value is None:
        return bool(term.get(NULLABLE))
    kind = term.get(FORMAT)
    return {"number": type(value) is int, "boolean": isinstance(value, bool), "url": isinstance(value, str) and bool(URL.match(value)),
            "algorithmId": isinstance(value, str) and bool(ALGORITHM_ID.match(value)),
            "requiredName": isinstance(value, str) and value in roles(), "role": isinstance(value, str) and value in roles(),
            "recipeId": isinstance(value, str) and bool(RECIPE_ID.match(value)),
            "deviationId": isinstance(value, str) and bool(DEVIATION_ID.match(value)),
            "className": isinstance(value, str) and bool(CLASS_NAME.match(value)),
            "operation": isinstance(value, str) and value in _operations(),
            "outputFormula": isinstance(value, str) and bool(OUTPUT_FORMULA.match(value)),
            "text": isinstance(value, (str, int, float))}.get(kind, False)


def _listed(value, values) -> bool:
    """A closed value is listed by equal value and type: 1 and 0 are not the booleans true and false."""
    return any(v == value and type(v) is type(value) for v in values)


def what_is(path: str, value=ALL):
    """path alone: that term or subtree. With a value: its one meaning; an unlisted value or a value of the wrong form is coded."""
    node = _node(path)
    if value is ALL:
        return node
    if not _is_term(node):
        raise GlossaryError(f"{UNKNOWN}: {path} is a section, not a term; valid here: {_children(node)}")
    if VALUES in node:
        if not _listed(value, node[VALUES]):
            raise GlossaryError(f"{UNKNOWN}: {path}: no value {value!r}; valid: {sorted(map(str, node[VALUES]))}")
        return node[VALUES][value]
    if not _fits(node, value):
        valid = f"; valid: {sorted(roles())}" if node.get(FORMAT) == "role" else ""
        raise GlossaryError(f"{UNKNOWN}: {path}: no value {value!r}{valid}" if valid else f"{UNKNOWN}: {path}: {value!r} is no {node.get(FORMAT)}")
    return roles()[value][MEANS] if node.get(FORMAT) == "role" else node[MEANS]


def _derived(path: str) -> bool:
    node = tree()
    for step in path.split("."):
        node = node.get(step) if isinstance(node, dict) else None
        if isinstance(node, dict) and node.get(DERIVED):
            return True
    return False


def _check(path: str, value) -> list[str]:
    try:
        if _derived(path):
            return [f"{UNKNOWN}: {path} is derived, never stored"]
        what_is(path, value)
    except GlossaryError as e:
        return [str(e)]
    return []


def _fields(path: str, row: dict) -> list[tuple[str, object]]:
    return [(f"{ALGORITHM}.{k}" if k in LEAF_ANYWHERE else f"{path}.{k}", v) for k, v in row.items()]


def entry_terms(raw: dict) -> list[tuple[str, object]]:
    """Every (path, value) of one catalogue entry."""
    found: list[tuple[str, object]] = _fields("algorithm.key", raw.get("key") or {})
    for section in ("required", "optional"):
        for row in raw.get(section) or []:
            found += _fields(f"{ALGORITHM}.{section}", row)
    for name, row in (raw.get("conditions") or {}).items():
        found += _fields(f"{ALGORITHM}.conditions.{name}", row)
    contract = raw.get("contract") or {}
    if contract:
        found.append(("algorithm.contract.key", contract.get("key")))
    for side in ("input", "output"):
        for name, value in (contract.get(side) or {}).items():
            plain = value["value"] if isinstance(value, dict) else value
            found.append((f"{ALGORITHM}.contract.{side}.{name}", plain))
            found += [("algorithm.contract.assumed", value["assumed"])] if isinstance(value, dict) else []
    for row in raw.get("sourcedOnly") or []:
        value = row.get("value")
        found += _fields("algorithm.sourcedOnly", {k: v for k, v in row.items() if k != "value"})
        if isinstance(value, dict):
            found += _fields("algorithm.sourcedOnly.value", value)
        else:
            found.append(("algorithm.sourcedOnly.value", value))
    for name, row in (raw.get("lifecycle") or {}).items():
        if name != RESET:
            found += _fields(f"{ALGORITHM}.lifecycle.{name}", row)
            continue
        for side, leaf in row.items():
            found.append((f"{ALGORITHM}.direction", side))
            found += _fields(f"{ALGORITHM}.lifecycle.{RESET}", leaf) if isinstance(leaf, dict) else []
    found += _fields(f"{ALGORITHM}.operations", raw.get("operations") or {})
    found += _fields("algorithm.provenance", raw.get("provenance") or {})
    for provider, overrides in (raw.get("providers") or {}).items():
        found.append(("algorithm.providers", provider))
        for at, value in (overrides or {}).items():
            found += _override(at, value)
    return found


def _override(at: str, value) -> list[tuple[str, object]]:
    """A provider override's path walks a list row by its name: required.nonce.spec means algorithm.required.spec; a whole row or mapping is read field by field."""
    steps = at.split(".")
    if steps[:2] == ["lifecycle", RESET] and len(steps) > 2 and steps[2] in tree()[ALGORITHM]["direction"][VALUES]:
        steps = [*steps[:2], *steps[3:]]
    if steps[0] in ("required", "optional") and len(steps) in (2, 3):
        if len(steps) == 2:
            return _fields(f"{ALGORITHM}.{steps[0]}", value) if isinstance(value, dict) else []
        steps = [steps[0], steps[2]]
    path = f"{ALGORITHM}." + ".".join(steps)
    if isinstance(value, dict):
        found: list[tuple[str, object]] = []
        for key, inner in value.items():
            found += [(f"{ALGORITHM}.{key}", inner)] if key in LEAF_ANYWHERE else _override(f"{'.'.join(steps)}.{key}", inner)
        return found
    return [(path, v) for v in (value if isinstance(value, list) else [value])]


def _expanded(path: str, value) -> list[tuple[str, object]]:
    return [(path, v) for v in value] if isinstance(value, list) else [(path, value)]


def term_problems(raw: dict) -> list[str]:
    """Each unlisted term or value of an entry, naming it."""
    found: list[str] = []
    for path, value in entry_terms(raw):
        for one_path, one in _expanded(path, value):
            found += _check(one_path, one)
    return [*dict.fromkeys(found)]


def provider_key_problems(raw: dict) -> list[str]:
    return [f"{UNKNOWN}: algorithm.providers: {p!r} is not <name> @ <build>" for p in raw.get("providers") or {} if not PROVIDER_KEY.match(p)]


def role_problems() -> list[str]:
    """Each role states how a value is made and how long it lives, by the closed words of make and lives; one word, or one per direction."""
    words, sides = tree()[ALGORITHM], tree()[ALGORITHM]["direction"][VALUES]
    found = []
    for name, role in roles().items():
        made, held = role.get(MAKE), role.get(LIVES)
        found += [f"{UNKNOWN}: algorithm.role.{name}: {MAKE} {made!r}"] * (made not in words[MAKE][VALUES])
        each = list(held.values()) if isinstance(held, dict) and set(held) == set(sides) else [held]
        found += [f"{UNKNOWN}: algorithm.role.{name}: {LIVES} {held!r}"] * any(not isinstance(v, str) or v not in words[LIVES][VALUES] for v in each)
        found += [f"{UNKNOWN}: algorithm.role.{name}: {GOES_TO} {call!r}" for calls in role.get(GOES_TO, {}).values() for call in calls if call not in words["required"]["passedTo"][VALUES]]
    return found


def direction_problems() -> list[str]:
    """Every operation has one direction of the closed words, and nothing else does."""
    held = tree()[ALGORITHM]["operations"]["value"][DIRECTIONS]
    found = [f"{UNKNOWN}: algorithm.operations.value: {op!r} has direction {held.get(op)!r}" for op in _operations() if held.get(op) not in tree()[ALGORITHM]["direction"][VALUES]]
    return found + [f"{UNKNOWN}: algorithm.operations.value: {op!r} is no operation" for op in held if op not in _operations()]


def recipe_terms(doc: dict) -> list[tuple[str, object]]:
    """Every (path, value) of recipes.yaml."""
    found: list[tuple[str, object]] = [(f"{RECIPE}.{k}", None) for k in doc]
    for recipe_id, raw in (doc.get("recipes") or {}).items():
        found.append((f"{RECIPE}.id", recipe_id))
        for key, value in (raw or {}).items():
            if key == "args":
                found.append((f"{RECIPE}.args", None))
                found += [(f"{RECIPE}.args.{k}", v) for arg in value for k, v in arg.items()]
            else:
                found.append((f"{RECIPE}.{key}", value))
    return found


def recipe_problems(doc: dict) -> list[str]:
    found: list[str] = []
    for path, value in recipe_terms(doc):
        found += _check(path, value) if value is not None else [] if _known(path) else [f"{UNKNOWN}: no term {path}"]
    return [*dict.fromkeys(found)]


def _known(path: str) -> bool:
    try:
        _node(path)
    except GlossaryError:
        return False
    return True


def _stray(section: str, keys) -> list[str]:
    return [f"{UNKNOWN}: no term {section}.{k}" for k in keys if not _known(f"{section}.{k}")]


def build_problems(doc: dict) -> list[str]:
    """Every key of provider-builds.yaml and of its rows a glossary term; each key <name> @ <build>, each origin a listed one."""
    found = _stray(BUILD, doc)
    for key, row in (doc.get("builds") or {}).items():
        found += [f"{UNKNOWN}: {BUILD}.builds: {key!r} is not <name> @ <build>"] * (not PROVIDER_KEY.match(key))
        found += _stray(BUILD, row) + _check(f"{BUILD}.origin", row.get("origin")) + _check(f"{BUILD}.name", row.get("name"))
    for name, row in (doc.get("providers") or {}).items():
        found += _check(f"{BUILD}.name", name) + _stray(f"{BUILD}.providers", row) + _set_problems(name, row.get("behaviour") or {})
        for registered in row.get("registers") or []:
            found += _stray(f"{BUILD}.providers.registers", registered)
            found += [p for one in registered.get("names") or [] for p in _check(f"{BUILD}.providers.registers.names", one)]
    return [*dict.fromkeys(found)]


def _set_problems(where: str, held: dict) -> list[str]:
    found = []
    for at, value in held.items():
        for path, one in _override(at, value):
            for one_path, each in _expanded(path, one):
                found += _check(one_path, each)
    return found if isinstance(held, dict) else [f"{UNKNOWN}: {where}: not a mapping"]


def deviation_problems(doc: dict) -> list[str]:
    """Every key of deviations.yaml a glossary term, each id of its form, each name an id, each set value a word its path allows."""
    found = _stray(DEVIATION, doc)
    for key, row in (doc.get("deviations") or {}).items():
        found += _check(f"{DEVIATION}.id", key) + _stray(DEVIATION, row)
        found += [p for name in row.get("names") or [] for p in _check(f"{DEVIATION}.names", name)]
        found += _set_problems(key, row.get("set") or {})
    return [*dict.fromkeys(found)]


def names_problems(doc: dict) -> list[str]:
    """Every key of algorithm-names.yaml a glossary term; each engine type a listed one."""
    found = _stray(NAMES, doc)
    for section in (NAMES, "sized", "transformations"):
        for engine, rows in (doc.get(section) or {}).items():
            found += _check(f"{NAMES}.engine", engine)
            if section == "sized":
                found += [p for row in rows.values() for p in _stray(f"{NAMES}.sized", row)]
            elif section == "transformations":
                found += _stray(f"{NAMES}.transformations", rows)
    return [*dict.fromkeys(found)]
