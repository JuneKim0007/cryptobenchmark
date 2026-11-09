from __future__ import annotations

from functools import cache

from cryptobench import paths
from cryptobench.document import AT_PATH, DocumentKind

CATALOG = paths.KEY_CONTRACT.path
SCHEMA_VERSION = 1
KEY_CONTRACT_DOC = DocumentKind("key contract", SCHEMA_VERSION, AT_PATH)


@cache
def _contract() -> dict:
    return KEY_CONTRACT_DOC.read(CATALOG)


def standard_key_interfaces() -> tuple[str, ...]:
    return tuple(_contract()["standardKeyInterfaces"])


def generated_key_formats() -> dict[str, str]:
    return dict(_contract()["generatedKeyFormats"])
