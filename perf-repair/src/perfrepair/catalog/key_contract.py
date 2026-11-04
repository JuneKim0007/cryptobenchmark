from __future__ import annotations

from functools import cache
from pathlib import Path

import yaml

from ..dto.document import AT_PATH, DocumentKind

CATALOG = Path(__file__).with_name("key-contract.yaml")
SCHEMA_VERSION = 1
KEY_CONTRACT_DOC = DocumentKind("key contract", SCHEMA_VERSION, AT_PATH)


@cache
def standard_key_interfaces() -> tuple[str, ...]:
    doc = yaml.safe_load(CATALOG.read_text())
    KEY_CONTRACT_DOC.check(doc, CATALOG)
    return tuple(doc["standardKeyInterfaces"])
