from __future__ import annotations

from functools import cache
from pathlib import Path

from ..dto.document import AT_PATH, DocumentKind

CATALOG = Path(__file__).with_name("key-contract.yaml")
SCHEMA_VERSION = 1
KEY_CONTRACT_DOC = DocumentKind("key contract", SCHEMA_VERSION, AT_PATH)


@cache
def _contract() -> dict:
    return KEY_CONTRACT_DOC.read(CATALOG)


def standard_key_interfaces() -> tuple[str, ...]:
    return tuple(_contract()["standardKeyInterfaces"])


def generated_key_formats() -> dict[str, str]:
    return dict(_contract()["generatedKeyFormats"])
