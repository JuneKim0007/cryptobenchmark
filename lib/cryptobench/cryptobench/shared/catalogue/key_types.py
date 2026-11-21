"""A provider spelling's catalogue entry and the key.type its provider's builds give it."""
from __future__ import annotations

from functools import cache

from .algorithms import Algorithms, Entry, algorithm_id, algorithms
from .names import Names, fold
from .provider_builds import ProviderBuilds, provider_builds
from .views import view_for


@cache
def _names() -> Names:
    return Names.load()


def entry_of(engine_type: str, name: str, names: Names | None = None, catalogue: Algorithms | None = None) -> Entry | None:
    canonical = (names or _names()).catalogued(engine_type, name)
    if not canonical.known:
        return None
    wanted = fold(algorithm_id(engine_type, canonical.name))
    return next((e for e in (catalogue or algorithms()).entries if fold(e.id) == wanted), None)


def key_type(engine_type: str, name: str, provider: str | None = None, names: Names | None = None,
             catalogue: Algorithms | None = None, builds: ProviderBuilds | None = None) -> str | None:
    """The entry's key.type as every build of the provider gives it, the base with no build; None: no entry, or builds that disagree."""
    entry = entry_of(engine_type, name, names, catalogue)
    if entry is None:
        return None
    builds = builds or provider_builds()
    keys = [provider] if provider in builds.builds else sorted(k for k, b in builds.builds.items() if b["name"] == provider)
    found = {view_for(entry.id, k, catalogue, builds)["key"]["type"] for k in keys} or {entry.raw["key"]["type"]}
    return found.pop() if len(found) == 1 else None


def same_key_type(a: str, b: str, names: Names | None = None) -> bool:
    names = names or _names()
    return fold(names.key_type(a).name) == fold(names.key_type(b).name)
