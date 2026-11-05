"""One algorithm's ids: the item is what java.security registers; canonical name, family and contract row are catalog facts."""
from __future__ import annotations

import re
from dataclasses import dataclass

from ..dto.grouping import SEPARATOR, qualified
from .groups import GroupCatalog, group_catalog
from .names import Names

# the rule of CaseName.kt, whose id parts the case id joins with "_"
UNSAFE = re.compile(r"[^A-Za-z0-9]")
PARAMETERS_TAG = r"(?:_p[0-9a-f]{8})?"


@dataclass(frozen=True)
class Identity:
    item: str
    algorithm: str
    canonical: str | None
    family: str
    row: str | None


def algorithm_id(engine_type: str, canonical: str) -> str:
    return SEPARATOR.join((engine_type, canonical))


def resolve(engine_type: str, name: str, provider: str, family: str, names: Names, catalog: GroupCatalog | None = None) -> Identity:
    """An unknown name keeps its registered spelling and has no canonical name or row: the model decides it."""
    found = names.catalogued(engine_type, name)
    canonical = found.name if found.known else None
    row = (catalog or group_catalog()).of(family, canonical)
    return Identity(qualified(engine_type, name, provider), algorithm_id(engine_type, canonical or name), canonical, family,
                    row.id if row else None)


def case_id_pattern(case: dict) -> re.Pattern:
    """A case id from its own fields; its parameters tag is a checksum of values no row keeps."""
    def part(value) -> str:
        return UNSAFE.sub("-", str(value))
    head = [case["type"], case["algorithm"], case["operation"], case["provider"]]
    head += [f"{tag}{case[key]}" for tag, key in (("k", "keySize"), ("i", "inputSize")) if case.get(key) is not None]
    head.append(case["phase"])
    tail = [case["variant"]] if case.get("variant") else []
    text = re.escape("_".join(map(part, head))) + PARAMETERS_TAG + "".join("_" + re.escape(part(t)) for t in tail)
    return re.compile(f"^{text}$")
