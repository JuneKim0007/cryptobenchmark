"""Known answers: algorithms/vectors/<family>.yaml, named by guide entries, plus a user's folder of the same layout, matched to cases by type,
name or alias, operation and key size; checked whole, and filled for the builds of one run."""
from __future__ import annotations

from pathlib import Path

from ..errors.input_error import InputError
from ..results.manifest import operations as engine_operations
from ..document.document import DocumentKind
from .algorithms import algorithms, algorithm_id
from .families import Families
from .guide_items import carried_recipes, parameter_tree
from .names import Names, fold
from .. import paths
from ..settings import bundled
from .provider_builds import provider_builds
from .recipes import load as load_recipes
from .views import view_for

SCHEMA_VERSION = 1
PACKAGED, USER = "packaged", "user"
FIELDS = {"id", "source", "type", "algorithm", "aliases", "operations", "compare", "key", "values", "input", "output"}
REQUIRED = {"id", "source", "type", "algorithm", "operations", "input", "output"}
INVALID = "vectors_invalid"
NEVER = "never"
FORWARD_OPERATIONS = ("ENCRYPT", "SIGN")


class VectorError(InputError):
    pass


VECTORS_DOC = DocumentKind("vectors", SCHEMA_VERSION, VectorError)


def _read_folder(folder: Path, origin: str, found: dict) -> None:
    known = Families.load().by_id
    for path in sorted(folder.glob("*.yaml")):
        if path.stem not in known:
            raise VectorError(f"{INVALID}: {path}: {path.stem} is no family of families.yaml")
        for vector in VECTORS_DOC.read(path, INVALID)["vectors"]:
            where = f"{path}: {vector.get('id')}"
            if stray := set(vector) - FIELDS:
                raise VectorError(f"{INVALID}: {where}: unknown fields {sorted(stray)}")
            if missing := REQUIRED - set(vector):
                raise VectorError(f"{INVALID}: {where}: missing {sorted(missing)}")
            if vector["id"] in found:
                raise VectorError(f"duplicate_id: {where} is already a vector of {found[vector['id']]['origin']}")
            found[vector["id"]] = {**vector, "origin": origin}


def load(user_folder: Path | None = None) -> dict[str, dict]:
    """A configured folder that does not exist stops the run: a typo must not read as no vectors."""
    found: dict[str, dict] = {}
    _read_folder(paths.repo().algorithms / "vectors", PACKAGED, found)
    if user_folder is not None:
        if not user_folder.is_dir():
            raise VectorError(f"vectors_folder_missing: {user_folder}")
        _read_folder(user_folder, USER, found)
    return found


def _refuse_randomized_forward(vector: dict, entry_id: str, conditions: dict) -> None:
    forward = set(vector["operations"]) & set(FORWARD_OPERATIONS)
    if forward and conditions.get("deterministic", {}).get("value") == NEVER:
        raise VectorError(f"vector_on_randomized_operation: {vector['id']}: {entry_id} never gives the same output of {sorted(forward)}; use a decrypt or verify vector")


def checked(vectors: dict[str, dict]) -> list[str]:
    """Every id a guide entry names exists and a randomized forward operation has none; returns the packaged vectors no entry names."""
    named: set[str] = set()
    for entry in algorithms().entries:
        listed = (entry.raw.get("knownVectors") or {}).get("ids") or []
        if len(set(listed)) != len(listed):
            raise VectorError(f"duplicate_id: {entry.id} names a vector twice: {listed}")
        for vector_id in listed:
            if vector_id not in vectors:
                raise VectorError(f"dangling_vector: {entry.id} names {vector_id}, in no vector file")
            named.add(vector_id)
            _refuse_randomized_forward(vectors[vector_id], entry.id, entry.raw["conditions"])
    packaged = {vector_id for vector_id, vector in vectors.items() if vector["origin"] == PACKAGED}
    return [f"orphan_vector: {vector_id} is named by no guide entry" for vector_id in sorted(packaged - named)]


def _matches(vector: dict, engine_type: str, identifier: str, key_sizes: set[int], names: Names, operations: dict) -> bool:
    """The oracle's match, for a user vector against one effective entry: type, name or alias, an operation of the type, key size."""
    if fold(vector["type"]) != fold(engine_type) or not set(vector["operations"]) & set(operations.get(engine_type) or ()):
        return False
    spellings = [vector["algorithm"], *(vector.get("aliases") or [])]
    if all(fold(algorithm_id(engine_type, names.canonical(engine_type, s).name)) != fold(identifier) for s in spellings):
        return False
    secret = (vector.get("key") or {}).get("secret")
    return not (secret and key_sizes and len(secret) * 4 not in key_sizes)


def _unexpressible(vector: dict, view: dict, recipes) -> str | None:
    """Why this build's way of passing parameters cannot carry what the vector fixes; none when it can."""
    values, carried = vector.get("values") or {}, carried_recipes(view)
    if not carried:
        return f"{sorted(values)}: this build takes no parameter object" if values else None
    recipe = recipes.by_id[carried[0]]
    for role, value in values.items():
        fixed = (recipe.get("fixes") or {}).get(role)
        if role not in recipes.roles(carried[0]) and fixed != value:
            return f"{role} {value}: {carried[0]} " + (f"fixes it at {fixed}" if fixed is not None else "has no place for it")
    for argument in recipe.get("args") or []:
        if argument.get("kind") == "bytes" and argument.get("role") not in values:
            raise VectorError(f"vector_incomplete: {vector['id']}: no {argument.get('role')}, which changes the output")
    return None


def _filled(vector: dict, name: str, provider: str, view: dict, recipes) -> dict:
    out = {k: vector[k] for k in ("id", "source", "origin", "type", "operations", "input", "output") } | {"algorithm": name, "provider": provider}
    out |= {k: vector[k] for k in ("key", "compare") if k in vector}
    reason = _unexpressible(vector, view, recipes)
    if reason:
        return {**out, "unexpressible": reason}
    carried = carried_recipes(view)
    if carried:
        rows = {r["name"]: r for r in view["required"]}
        out["parameters"] = parameter_tree(carried[0], rows, recipes.by_id, vector.get("values") or {})
    return out


def filled(effective: dict, platform: str | None, user_folder: Path | None = None) -> tuple[dict, list[str]]:
    """The run's known-answers document: each listed vector once per provider, in the form that provider takes."""
    vectors = load(user_folder)
    warnings = checked(vectors)
    names, builds, recipes = Names.load(), provider_builds(), load_recipes()
    artifacts = {b.get("alias"): b["artifact"] for b in effective.get(bundled.KEY) or []}
    known = {fold(e.id) for e in algorithms().entries}
    user = [v for v in vectors.values() if v["origin"] == USER]
    operations, reached = engine_operations(), set()
    out: list[dict] = []
    for provider, types in (effective.get("providers") or {}).items():
        build, _ = builds.nearest(provider, platform, artifacts.get(provider))
        for engine_type, entries in types.items():
            for name in dict.fromkeys(k.split("@")[0] for k in entries):
                canonical = names.canonical(engine_type, name)
                identifier = algorithm_id(engine_type, canonical.name)
                if fold(identifier) not in known:
                    continue
                view = view_for(identifier, build, builds=builds) if build else view_for(identifier)
                key_sizes = {size for k, entry in entries.items() if k.split("@")[0] == name for size in (entry or {}).get("keySizes") or []}
                key_sizes |= {canonical.keySize} if canonical.keySize else set()
                mine = [v for v in user if _matches(v, engine_type, identifier, key_sizes, names, operations)]
                for vector in mine:
                    _refuse_randomized_forward(vector, identifier, view.get("conditions") or {})
                reached |= {v["id"] for v in mine}
                out += [_filled(v, name, provider, view, recipes) for v in [vectors[i] for i in (view.get("knownVectors") or {}).get("ids") or []] + mine]
    warnings += [f"orphan_vector: {v['id']} matches no case of this run by type, name or alias, operation and key size" for v in user if v["id"] not in reached]
    return {"schemaVersion": SCHEMA_VERSION, "vectors": out}, warnings


def coverage(cases: list[dict]) -> tuple[list[str], bool]:
    """One line per family of what --check's known-answer oracle did; whether any vector was really compared."""
    names = Names.load()
    by_id = {fold(e.id): e for e in algorithms().entries}
    counts: dict[str, dict[str, int]] = {}
    for record in cases:
        answer = (record.get("oracles") or {}).get("knownAnswer")
        if answer is None:
            continue
        case = record["case"]
        entry = by_id.get(fold(algorithm_id(case["type"], names.canonical(case["type"], case["algorithm"]).name)))
        family = entry.family if entry else "unidentified"
        if answer["verdict"] in ("pass", "fail"):
            state = {"pass": "passed", "fail": "failed"}[answer["verdict"]]
        elif str(answer.get("reason", "")).startswith("vector_not_expressible"):
            state = "not expressible"
        elif entry is not None and "knownVectors" in entry.raw and not entry.raw["knownVectors"]:
            state = "none by choice"
        elif entry is None or "knownVectors" not in entry.raw:
            state = "not listed"
        else:
            state = "not checkable"
        counts.setdefault(family, {}).setdefault(state, 0)
        counts[family][state] += 1
    lines = [f"knownVectors: {family}: " + ", ".join(f"{n} {state}" for state, n in sorted(states.items())) for family, states in sorted(counts.items())]
    return lines, any(state in ("passed", "failed") for states in counts.values() for state in states)
