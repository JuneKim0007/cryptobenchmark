"""catalog/algorithms/recipes.yaml: how each parameter object a catalogue row names is made, by id; read and checked whole."""
from __future__ import annotations

from dataclasses import dataclass
from functools import cache
from pathlib import Path

from ..dto.coded import InputError
from ..dto.document import AT_PATH, DocumentKind
from .glossary import direction_problems, recipe_problems, role_problems

CATALOG = Path(__file__).with_name("algorithms") / "recipes.yaml"
SCHEMA_VERSION = 1
INVALID = "recipes_invalid"
FORMS = (("class", "args"), ("factory", "args", "steps"), ("builder",))
RECIPE, CONSTANT, ENUM = "recipe", "constant", "enum"


class RecipeError(InputError):
    pass


RECIPES_DOC = DocumentKind("recipes", SCHEMA_VERSION, INVALID + ": " + AT_PATH, RecipeError)


@dataclass(frozen=True)
class Recipes:
    by_id: dict[str, dict]

    def roles(self, recipe_id: str) -> set[str]:
        """Every role an object of this recipe passes, nested recipes included."""
        found: set[str] = set()
        for arg in self.by_id[recipe_id].get("args") or []:
            found |= self.roles(arg[RECIPE]) if arg.get("kind") == RECIPE else {arg["role"]} if "role" in arg else set()
        return found

    def built_by_hand(self, recipe_id: str) -> bool:
        return "builder" in self.by_id[recipe_id]


def _form_problems(recipe_id: str, raw) -> list[str]:
    if not isinstance(raw, dict):
        return [f"{recipe_id}: not a mapping"]
    keys = set(raw)
    if not any(keys == set(form) for form in FORMS):
        return [f"{recipe_id}: fields {sorted(keys)} are none of the forms {[list(f) for f in FORMS]}"]
    return []


def _arg_problems(recipe_id: str, raw: dict, known: set[str]) -> list[str]:
    found = []
    for i, arg in enumerate(raw.get("args") or []):
        kind = arg.get("kind")
        if kind == RECIPE and arg.get(RECIPE) not in known:
            found.append(f"{recipe_id} arg {i}: nested recipe {arg.get(RECIPE)!r} is no recipe")
        if kind in (CONSTANT, ENUM) and ("value" not in arg or "role" in arg):
            found.append(f"{recipe_id} arg {i}: a {kind} holds a value and no role")
        if kind not in (CONSTANT, ENUM, RECIPE) and "role" not in arg:
            found.append(f"{recipe_id} arg {i}: a {kind} names its role")
    return found


def load(path: Path = CATALOG) -> Recipes:
    doc = RECIPES_DOC.read(path, INVALID)
    raw = doc.get("recipes")
    if not isinstance(raw, dict):
        raise RecipeError(f"{INVALID}: {path}: recipes is not a mapping")
    problems = recipe_problems(doc) + role_problems() + direction_problems() + [p for i, r in raw.items() for p in _form_problems(i, r)]
    problems += [p for i, r in raw.items() if isinstance(r, dict) for p in _arg_problems(i, r, set(raw))]
    if problems:
        raise RecipeError(f"{INVALID}: " + "; ".join(problems))
    return Recipes(raw)


@cache
def recipes() -> Recipes:
    return load()
