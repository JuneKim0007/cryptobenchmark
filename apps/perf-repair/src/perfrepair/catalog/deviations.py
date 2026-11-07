"""algorithms/deviations.yaml: a fact shared by a set of names and builds, stated once; what an entry's providers section holds after it and the provider-wide behaviours apply."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..dto.coded import InputError
from ..dto.document import AT_PATH, DocumentKind
from .glossary import deviation_problems
from .names import fold
from .overrides import override_parent
from .provider_builds import ProviderBuilds

CATALOG = Path(__file__).with_name("algorithms") / "deviations.yaml"
SCHEMA_VERSION = 1
INVALID = "deviations_invalid"
PROVIDERS = "providers"


class DeviationError(InputError):
    pass


DEVIATIONS_DOC = DocumentKind("deviations", SCHEMA_VERSION, INVALID + ": " + AT_PATH, DeviationError)


@dataclass(frozen=True)
class Deviation:
    id: str
    builds: tuple[str, ...]
    names: tuple[str, ...]
    set: dict


@dataclass(frozen=True)
class Deviations:
    all: tuple[Deviation, ...]
    builds: ProviderBuilds

    def __post_init__(self):
        held: dict[str, list[Deviation]] = {}
        for deviation in self.all:
            for name in deviation.names:
                held.setdefault(fold(name), []).append(deviation)
        object.__setattr__(self, "_by_name", held)

    def stated(self, identifier: str, raw: dict) -> dict:
        """Per build, what the provider-wide behaviours and this file state of one entry; a behaviour's field the entry has no parent for is skipped."""
        found = {build: {p: v for p, v in values.items() if override_parent(raw, p) is not None}
                 for build, values in self.builds.behaviours(identifier).items()}
        for deviation in self._by_name.get(fold(identifier), ()):
            for build in deviation.builds:
                found.setdefault(build, {}).update(deviation.set)
        return found

    def overlaid(self, identifier: str, raw) -> object:
        """The entry with `providers` holding every build's differences: the entry's own win, each build's paths in order, as apply_override needs one order."""
        if not isinstance(raw, dict) or not isinstance(raw.get(PROVIDERS), dict):
            return raw
        merged = self.stated(identifier, raw)
        for build, own in raw[PROVIDERS].items():
            merged[build] = {**merged.get(build, {}), **(own if isinstance(own, dict) else {})} if isinstance(own, dict) else own
        return {**raw, PROVIDERS: {b: dict(sorted(o.items())) if isinstance(o, dict) else o for b, o in sorted(merged.items()) if o or not isinstance(o, dict)}}

    def problems(self, identifiers: set[str]) -> list[str]:
        """A name no catalogue holds, or two deviations stating one path of one name on one build."""
        found = [f"deviation {d.id}: {n} is no entry of the catalogues" for d in self.all for n in d.names if fold(n) not in identifiers]
        seen: dict[tuple[str, str, str], str] = {}
        for d in self.all:
            for key in ((fold(n), b, p) for n in d.names for b in d.builds for p in d.set):
                if key in seen:
                    found.append(f"deviations {seen[key]} and {d.id} both state {key[2]} of {key[0]} on {key[1]}")
                seen[key] = d.id
        return found


def load(path: Path, builds: ProviderBuilds) -> Deviations:
    doc = DEVIATIONS_DOC.read(path, INVALID)
    problems = deviation_problems(doc)
    all_ = []
    for key, raw in (doc.get("deviations") or {}).items():
        try:
            all_.append(Deviation(key, builds.expanded(raw["builds"]), tuple(raw["names"]), raw["set"]))
        except InputError as e:
            problems.append(f"deviation {key}: {e}")
    if problems:
        raise DeviationError(f"{INVALID}: {path}: " + "; ".join(problems))
    return Deviations(tuple(all_), builds)
