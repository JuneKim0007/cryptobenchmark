"""The requirements file written with a capture: same stamp, indexed by (provider, type, algorithm)."""
from __future__ import annotations

from functools import cached_property
from pathlib import Path

from ....dto.document import DocumentKind
from ....files import read_versioned

REQUIREMENTS_DOC = DocumentKind("requirements", 1)


class Requirements:

    def __init__(self, document: dict):
        self._document = document

    @classmethod
    def load(cls, path: Path) -> "Requirements":
        return cls(read_versioned(REQUIREMENTS_DOC, path))

    @classmethod
    def beside(cls, capture: Path) -> "Requirements":
        capture = Path(capture)
        return cls.load(capture.with_name("requirements_" + capture.name.rsplit("_", 1)[-1]))

    @property
    def captured_at_millis(self) -> int:
        return self._document["capturedAtMillis"]

    @property
    def device_clock_millis(self) -> int:
        return self._document["deviceClockMillis"]

    @property
    def services(self) -> list[dict]:
        return self._document.get("services") or []

    def of(self, provider: str, engine_type: str, algorithm: str) -> dict | None:
        return self._index.get((provider, engine_type, algorithm))

    @cached_property
    def _index(self) -> dict[tuple, dict]:
        return {(s["provider"], s["type"], s["algorithm"]): s for s in self.services}
