"""Scopes and replacements over tests/fixtures/edit_app, built from the dto shapes."""
from __future__ import annotations

import hashlib
from pathlib import Path

from perfrepair.dto.replacement import Edit, Replacement
from perfrepair.dto.site import Scope, scope_id

APP = "demo"
ROOT = Path(__file__).parent / "fixtures" / "edit_app"
JAVA = "src/main/java/demo/Vault.java"
KOTLIN = "src/main/kotlin/demo/Seal.kt"


def scope(file: str, function: str, call: str, head: str = "getInstance(", line_shift: int = 0, **extra) -> Scope:
    """The function declared by the line holding `function`, ending at its 4-space `}`; the call on the first `head` line."""
    lines = (ROOT / file).read_text().splitlines()
    start = next(i for i, l in enumerate(lines, 1) if function in l)
    end = next(i for i in range(start, len(lines) + 1) if lines[i - 1] == "    }")
    line = next(i for i in range(start, end + 1) if head in lines[i - 1]) + line_shift
    return Scope(scope_id(APP, file, function, line, call), APP, file, line, call, function, start, end,
                 "Cipher", None, None, "default", **extra)


def replace(s: Scope, *edits: Edit, option: str = "7") -> Replacement:
    return Replacement(s.id, "replace", option, tuple(edits), (), "faster")


def provider(name: str) -> Edit:
    return Edit("set_provider", provider=name)


def algorithm(name: str) -> Edit:
    return Edit("set_algorithm", algorithm=name)


def pins(**values) -> Edit:
    return Edit("pin_parameters", parameters=values)


def digests(root: Path = ROOT) -> dict[str, str]:
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file()}
