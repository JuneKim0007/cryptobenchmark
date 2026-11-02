"""Whether a type name at an offset is the platform security class: fully qualified, imported, or wildcard-imported."""
from __future__ import annotations

import re

from ..source.lexer import Code

PACKAGES = ("java.security", "javax.crypto")

_IMPORT = re.compile(r"^[ \t]*import\s+([\w.]+?)(\.\*)?(?:\s+as\s+(\w+))?\s*;?[ \t]*$", re.M)
_QUALIFIER = re.compile(r"([\w.]+?)\s*\.\s*$")


def _imports(code: Code) -> tuple[dict[str, str], set[str]]:
    named, wildcards = {}, set()
    for m in _IMPORT.finditer(code.masked):
        path, star, alias = m.groups()
        if star:
            wildcards.add(path)
        else:
            named[alias or path.rsplit(".", 1)[-1]] = path
    return named, wildcards


def import_reason(code: Code, type_name: str, offset: int) -> str | None:
    """None when the name at offset is the platform class; otherwise why it is not."""
    q = _QUALIFIER.search(code.masked[max(0, offset - 200):offset])
    if q:
        return None if q.group(1) in PACKAGES else "other_qualifier"
    if re.search(rf"\b(?:class|interface|object|enum|typealias)\s+{re.escape(type_name)}\b", code.masked):
        return "local_declaration"
    named, wildcards = _imports(code)
    if type_name in named:
        return None if named[type_name] in {f"{p}.{type_name}" for p in PACKAGES} else "other_import"
    return None if wildcards & set(PACKAGES) else "not_imported"
