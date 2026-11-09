"""sdk-constants.yaml read and checked once: a platform constant's expression → the name it stands for."""
from __future__ import annotations

from functools import cache
from pathlib import Path

from cryptobench import paths
from cryptobench.document import AT_PATH, DocumentKind

CATALOG = paths.SDK_CONSTANTS.path
SCHEMA_VERSION = 1
SDK_CONSTANTS_DOC = DocumentKind("sdk constants", SCHEMA_VERSION, AT_PATH)


@cache
def sdk_constants(path: Path = CATALOG) -> dict[str, str]:
    doc = SDK_CONSTANTS_DOC.read(path)
    sources = doc.get("sources") or {}
    bad = [k for k, v in (doc.get("constants") or {}).items()
           if not isinstance(v, dict) or not isinstance(v.get("value"), str) or v.get("source") not in sources]
    if bad:
        raise ValueError(f"{path}: constants {bad} need a value and a listed source")
    return {k: v["value"] for k, v in doc["constants"].items()}
