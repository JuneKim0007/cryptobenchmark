"""provider-builds.yaml: every provider build the catalogues' measured facts ran on, its key and what it says of itself; a behaviour true of a provider, stated once; a name resolves to a key or is refused."""
from __future__ import annotations

from dataclasses import dataclass, field
from functools import cache
from pathlib import Path

from ..dto.coded import InputError
from ..dto.document import AT_PATH, DocumentKind
from .glossary import build_problems

CATALOG = Path(__file__).with_name("provider-builds.yaml")
SCHEMA_VERSION = 1
UNKNOWN = "provider_build_unknown"
SEPARATOR = " @ "
PLATFORM, BUNDLED, HOST = "platform", "bundled", "host"


class ProviderBuildError(InputError):
    pass


BUILDS_DOC = DocumentKind("provider-builds", SCHEMA_VERSION, UNKNOWN + ": " + AT_PATH, ProviderBuildError)


def build_key(name: str, origin: str, *, sdk_int: int | None = None, artifact: str | None = None, jdk: int | None = None) -> str:
    """The key of one build from what a probe records: a platform provider by its Android level, a bundled copy by its artifact, a host provider by its JDK."""
    where = {PLATFORM: f"android-{sdk_int}" if sdk_int else None, BUNDLED: artifact, HOST: f"jdk-{jdk}" if jdk else None}.get(origin)
    if where is None:
        raise ProviderBuildError(f"{UNKNOWN}: {name}: origin {origin!r} with sdk_int={sdk_int}, artifact={artifact}, jdk={jdk} names no build")
    return f"{name}{SEPARATOR}{where}"


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


def load(path: Path = CATALOG) -> ProviderBuilds:
    doc = BUILDS_DOC.read(path, UNKNOWN)
    problems = build_problems(doc)
    if problems:
        raise ProviderBuildError(f"{UNKNOWN}: {path}: " + "; ".join(problems))
    return ProviderBuilds(doc["builds"], doc.get("providers") or {})


@cache
def provider_builds() -> ProviderBuilds:
    return load()
