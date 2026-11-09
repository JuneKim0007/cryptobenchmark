"""provider-builds.yaml: every provider build the catalogues' measured facts ran on, its key and what it says of itself; a behaviour true of a provider, stated once; a name resolves to a key or is refused."""
from __future__ import annotations

from .paths import DATA
import re
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path

from ..coded import InputError
from ..document import AT_PATH, DocumentKind
from .glossary import build_problems

CATALOG = DATA / "provider-builds.yaml"
SCHEMA_VERSION = 1
UNKNOWN = "provider_build_unknown"


class ProviderBuildError(InputError):
    pass


BUILDS_DOC = DocumentKind("provider-builds", SCHEMA_VERSION, UNKNOWN + ": " + AT_PATH, ProviderBuildError)


@dataclass(frozen=True)
class ProviderBuilds:
    builds: dict[str, dict]
    providers: dict[str, dict] = field(default_factory=dict)

    def expanded(self, words: list[str]) -> tuple[str, ...]:
        """Each word a build key, or a provider name meaning every build of it; another word is coded."""
        found: list[str] = []
        for word in words:
            named = [word] if word in self.builds else sorted(k for k, b in self.builds.items() if b["name"] == word)
            if not named:
                raise ProviderBuildError(f"{UNKNOWN}: {word!r} is no build or provider")
            found += named
        return tuple(found)

    def behaviours(self, identifier: str) -> dict[str, dict]:
        """Per build, the behaviour of a provider that registers the id there."""
        found = {}
        for provider in self.providers.values():
            for row in provider["registers"]:
                if identifier in row["names"]:
                    found.update({build: provider["behaviour"] for build in self.expanded(row["builds"])})
        return found

    def resolve(self, provider: str) -> str:
        """A build key as it stands; a bare name only when one build carries it (BundledBC); anything else is refused, naming the candidates."""
        if provider in self.builds:
            return provider
        named = sorted(k for k, b in self.builds.items() if b["name"] == provider)
        if len(named) == 1:
            return named[0]
        raise ProviderBuildError(f"{UNKNOWN}: {provider!r} is {'one of ' + str(named) if named else 'no build the catalogues have measured'}")

    def nearest(self, provider: str, platform: str | None, artifact: str | None) -> tuple[str | None, bool]:
        """The build of a provider here and whether it is exactly this one; else the nearest at or below this platform, else its latest."""
        keys = sorted(k for k, b in self.builds.items() if b["name"] == provider)
        for exact in (f"{provider} @ {platform}", f"{provider} @ {artifact}"):
            if exact in keys:
                return exact, True
        match = re.fullmatch(r"(\w+)-(\d+)", platform or "")
        same_kind = sorted((int(k.rsplit("-", 1)[1]), k) for k in keys if match and re.search(rf" @ {match[1]}-\d+$", k))
        if same_kind:
            return ([k for n, k in same_kind if n <= int(match[2])] or [same_kind[0][1]])[-1], False
        return (keys[-1], False) if keys else (None, False)


def load(path: Path = CATALOG) -> ProviderBuilds:
    doc = BUILDS_DOC.read(path, UNKNOWN)
    problems = build_problems(doc)
    if problems:
        raise ProviderBuildError(f"{UNKNOWN}: {path}: " + "; ".join(problems))
    return ProviderBuilds(doc["builds"], doc.get("providers") or {})


@cache
def provider_builds() -> ProviderBuilds:
    return load()
