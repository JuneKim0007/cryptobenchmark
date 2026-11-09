"""What the guide says for exactly the items of one effective.yaml, at the builds this device runs: preparation's guide.yaml."""
from __future__ import annotations

from .algorithms import algorithms, algorithm_id
from .names import Names
from .provider_builds import ProviderBuilds, provider_builds
from .recipes import load as load_recipes
from .views import view_for

SCHEMA_VERSION = 1
ANDROID = " @ android-"


def build_of(provider: str, sdk: int | None, artifact: str | None, builds: ProviderBuilds) -> tuple[str | None, bool]:
    """The build key of a provider here, and whether it is exactly this one; without one, the nearest Android build at or below this sdk."""
    keys = [k for k, b in builds.builds.items() if b["name"] == provider]
    exact = f"{provider}{ANDROID}{sdk}" if sdk else f"{provider} @ {artifact}"
    if exact in keys:
        return exact, True
    android = sorted((int(k.split(ANDROID)[1]), k) for k in keys if ANDROID in k)
    if sdk and android:
        return ([k for s, k in android if s <= sdk] or [android[0][1]])[-1], False
    return (sorted(keys)[-1], False) if keys else (None, False)


def _argument(argument: dict, rows: dict, recipes: dict):
    kind = argument.get("kind")
    if kind == "constant":
        return argument["value"]
    if kind == "recipe":
        return _tree(argument["recipe"], rows, recipes)
    if kind == "enum":
        return {"field": argument["value"]}
    row = rows.get(argument.get("role"), {})
    if kind == "bytes":
        if not row.get("bytes"):
            raise LookupError(f"{argument.get('role')} has no length")
        return f"fresh({row['bytes']})"
    if "value" in argument:
        return argument["value"]
    if "value" in row:
        return row["value"]
    raise LookupError(f"{argument.get('role')} has no value")


def _tree(recipe_id: str, rows: dict, recipes: dict) -> dict:
    recipe = recipes[recipe_id]
    if "class" not in recipe:
        raise LookupError(f"{recipe_id} is not a constructor")
    return {"class": recipe["class"], "arguments": [_argument(a, rows, recipes) for a in recipe.get("args") or []]}


def _item(view: dict, build: str | None, exact: bool, recipes: dict) -> dict:
    rows = {r["name"]: r for r in view["required"]}
    item: dict = {"build": build, "exactBuild": exact}
    carried = sorted({r["recipe"] for r in view["required"] if r.get("recipe") and r.get("passedTo") == "init"})
    if len(carried) > 1:
        return {**item, "problem": f"guide_recipe_unbuildable: {carried} are several objects for one init"}
    if carried:
        try:
            item["parameters"] = _tree(carried[0], rows, recipes)
        except LookupError as gap:
            return {**item, "problem": f"guide_recipe_unbuildable: {gap}"}
    key_bytes = (view.get("key") or {}).get("bytes")
    if key_bytes:
        item["keySizes"] = sorted(b * 8 for b in key_bytes)
    return item


def guide_items(effective: dict, sdk: int | None) -> dict:
    """An item the guide does not hold is left out, and preparation logs and drops it."""
    names, builds, recipes = Names.load(), provider_builds(), load_recipes().by_id
    known = {e.id.upper() for e in algorithms().entries}
    artifacts = {b.get("alias"): b["artifact"] for b in effective.get("bundledProviders") or []}
    items: dict = {}
    for provider, types in (effective.get("providers") or {}).items():
        build, exact = build_of(provider, sdk, artifacts.get(provider), builds)
        for engine_type, entries in types.items():
            for key in entries:
                name = key.split("@")[0]
                identifier = algorithm_id(engine_type, names.canonical(engine_type, name).name)
                if identifier.upper() not in known:
                    continue
                view = view_for(identifier, build, builds=builds) if build else view_for(identifier)
                items.setdefault(provider, {}).setdefault(engine_type, {})[name] = _item(view, build, exact, recipes)
    return {"schemaVersion": SCHEMA_VERSION, "items": items}
