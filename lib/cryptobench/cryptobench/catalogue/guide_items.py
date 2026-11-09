"""What the guide says for exactly the items of one effective.yaml, at the builds this device runs: preparation's guide.yaml."""
from __future__ import annotations

from .algorithms import KEY_PROVIDER, algorithms, algorithm_id
from .names import Names, fold
from .provider_builds import provider_builds
from .recipes import load as load_recipes
from .views import view_for

SCHEMA_VERSION = 1


def _argument(argument: dict, rows: dict, recipes: dict, fixed: dict):
    kind, role = argument.get("kind"), argument.get("role")
    if kind == "constant":
        return argument["value"]
    if kind == "recipe":
        return parameter_tree(argument["recipe"], rows, recipes, fixed)
    if kind == "enum":
        return {"field": argument["value"]}
    if role in fixed:
        return {"hex": fixed[role]} if kind == "bytes" else fixed[role]
    row = rows.get(role, {})
    if kind == "bytes":
        if not row.get("bytes"):
            raise LookupError(f"{role} has no length")
        return f"fresh({row['bytes']})"
    if "value" in argument:
        return argument["value"]
    if "value" in row:
        return row["value"]
    raise LookupError(f"{role} has no value")


def parameter_tree(recipe_id: str, rows: dict, recipes: dict, fixed: dict | None = None) -> dict:
    """The tree preparation binds: a recipe's object, each value from what `fixed` states, else the entry's row."""
    recipe = recipes[recipe_id]
    if "class" not in recipe:
        raise LookupError(f"{recipe_id} is not a constructor")
    return {"class": recipe["class"], "arguments": [_argument(a, rows, recipes, fixed or {}) for a in recipe.get("args") or []]}


def carried_recipes(view: dict) -> list[str]:
    """The recipes of the object or objects this build's init takes."""
    return sorted({r["recipe"] for r in view["required"] if r.get("recipe") and r.get("passedTo") == "init"})


def _item(view: dict, build: str | None, exact: bool, recipes: dict) -> dict:
    rows = {r["name"]: r for r in view["required"]}
    item: dict = {"build": build, "exactBuild": exact}
    if (view.get("key") or {}).get("origin") == KEY_PROVIDER:
        return {**item, "refused": "key_inside_provider: this provider keeps its own keys; the harness cannot create them yet"}
    carried = carried_recipes(view)
    if len(carried) > 1:
        return {**item, "problem": f"guide_recipe_unbuildable: {carried} are several objects for one init"}
    if carried:
        try:
            item["parameters"] = parameter_tree(carried[0], rows, recipes)
        except LookupError as gap:
            return {**item, "problem": f"guide_recipe_unbuildable: {gap}"}
    key_bytes = (view.get("key") or {}).get("bytes")
    if key_bytes:
        item["keySizes"] = sorted(b * 8 for b in key_bytes)
    return item


def guide_items(effective: dict, platform: str | None) -> dict:
    """An item the guide does not hold is left out, and preparation logs and drops it."""
    names, builds, recipes = Names.load(), provider_builds(), load_recipes().by_id
    known = {fold(e.id) for e in algorithms().entries}
    artifacts = {b.get("alias"): b["artifact"] for b in effective.get("bundledProviders") or []}
    items: dict = {}
    for provider, types in (effective.get("providers") or {}).items():
        build, exact = builds.nearest(provider, platform, artifacts.get(provider))
        for engine_type, entries in types.items():
            for key in entries:
                name = key.split("@")[0]
                identifier = algorithm_id(engine_type, names.canonical(engine_type, name).name)
                if fold(identifier) not in known:
                    continue
                view = view_for(identifier, build, builds=builds) if build else view_for(identifier)
                items.setdefault(provider, {}).setdefault(engine_type, {})[name] = _item(view, build, exact, recipes)
    return {"schemaVersion": SCHEMA_VERSION, "items": items}
