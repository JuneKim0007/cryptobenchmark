"""The probe file parsed once; each view is built on first use."""
from __future__ import annotations

from functools import cached_property
from pathlib import Path
from typing import Callable

from ....catalog.names import Names
from ....files import read_document
from ._index import ProbeIndex, index_of
from ._names import merged
from ._services import attributes_of, class_names_of, generator_kind


# the capture's origin of a provider providers.bundled installed; an older capture without origin is all platform
BUNDLED_ORIGIN = "bundled"


class Probe:

    def __init__(self, document: dict, source: str = "probe"):
        self._document, self._source = document, source

    @classmethod
    def load(cls, path: Path) -> "Probe":
        return cls(read_document(path), str(path))

    @cached_property
    def index(self) -> ProbeIndex:
        return index_of(self._document, self._source)

    def names(self, base: Names) -> Names:
        return merged(base, self._document)

    def attributes(self, provider: str, engine_type: str, algorithm: str) -> dict:
        return self._attributes.get((provider, engine_type, algorithm), {})

    def class_name(self, provider: str, engine_type: str, algorithm: str) -> str | None:
        return self._class_names.get((provider, engine_type, algorithm))

    def generator_kind(self, names: Names) -> Callable[[str], str | None]:
        return generator_kind(self._document, names)

    def platform_providers(self) -> frozenset[str]:
        """The names the device registers itself, without the ones providers.bundled installed."""
        return frozenset(p["name"] for p in self._document.get("providers") or [] if p.get("origin") != BUNDLED_ORIGIN)

    def harness_artifacts(self) -> dict[str, str]:
        """Per provider providers.bundled installed, its artifact's group:name; an older capture names none."""
        return {p["name"]: ":".join(p.get("artifact", "").split(":")[:2]) for p in self._document.get("providers") or []
                if p.get("origin") == BUNDLED_ORIGIN}

    @cached_property
    def _attributes(self) -> dict[tuple, dict]:
        return attributes_of(self._document)

    @cached_property
    def _class_names(self) -> dict[tuple, str | None]:
        return class_names_of(self._document)
