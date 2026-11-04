"""The operations the harness times per engine type: cryptobenchmark's own engine-operations.yaml, the one list both
sides read; a type that falls back to TYPE_DEFAULT has none, so it cannot be measured."""
from __future__ import annotations

from functools import cache
from pathlib import Path

import yaml

from ..dto.document import AT_PATH, DocumentKind

REPO = Path(__file__).resolve().parents[4]
HARNESS_OPERATIONS = REPO / "modules/preparation/src/main/resources/io/github/junekim0007/cryptobench/preparation/engine/engine-operations.yaml"
OPERATIONS_DOC = DocumentKind("harness operations", 1, AT_PATH)


@cache
def _table(path: Path = HARNESS_OPERATIONS) -> dict[str, tuple[str, ...]]:
    doc = yaml.safe_load(Path(path).read_text())
    OPERATIONS_DOC.check(doc, path)
    return {t.upper(): tuple(ops) for t, ops in (doc.get("types") or {}).items()}


def operations_of(engine_type: str) -> tuple[str, ...]:
    """Empty: the type falls back to TYPE_DEFAULT, whose invocation times nothing."""
    return _table().get(engine_type.upper(), ())
