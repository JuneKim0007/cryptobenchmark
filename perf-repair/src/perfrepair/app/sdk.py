"""minSdk and targetSdk of the application module: a literal, a catalog version, or a named Gradle property."""
from __future__ import annotations

import re
from pathlib import Path

from ..dto.language import of_build_file
from .lexer import mask, matching
from .sources import CATALOG

APPLICATION = re.compile(r"\bcom\.android\.application\b|\bplugins\.android\.application\b")
_DEFAULT_CONFIG = re.compile(r"\bdefaultConfig\s*\{")
_CATALOG_REF = re.compile(r"libs\.versions\.([\w.]+?)\.get\(\)")
_LAST_NAME = re.compile(r"(\w+)\W*$")


def _value_expr(text: str, key: str) -> str | None:
    m = re.search(rf"\b{key}(?:Version)?\b(?:\s*=\s*|\s*\(\s*|[ \t]+)([^\n]+)", text)
    return m.group(1).strip().rstrip(") ").strip("'\"") if m else None


def _named(name: str, texts: list[str]) -> set[int]:
    pattern = re.compile(rf"""(?:^|[\s.(])["']?{re.escape(name)}["']?\s*[=:]\s*["']?(\d+)["']?""", re.M)
    return {int(v) for t in texts for v in pattern.findall(t)}


def _resolve(expr: str, texts: list[str]) -> int | None:
    if expr.isdigit():
        return int(expr)
    ref = _CATALOG_REF.search(expr)
    if ref:
        dotted = ref.group(1)
        values = set().union(*(_named(n, texts) for n in {dotted, dotted.replace(".", "-"), dotted.replace(".", "_")}))
    else:
        last = _LAST_NAME.search(expr.replace(".get()", "").replace(".toInt()", ""))
        values = _named(last.group(1), texts) if last else set()
    return values.pop() if len(values) == 1 else None


def _block(text: str) -> str:
    m = _DEFAULT_CONFIG.search(text)
    if not m:
        return text
    close = matching(text, m.end() - 1)
    return text[m.end():close] if close else text


def sdk_levels(build_files: list[Path]) -> dict[str, int | None]:
    """{'minSdk', 'targetSdk'}: one value when every application module agrees, else None."""
    texts = {p: mask(p.read_text(errors="replace"), of_build_file(p.name), strings=False)
             for p in build_files if p.name != CATALOG}
    catalogs = [p.read_text(errors="replace") for p in build_files if p.name == CATALOG]
    every = [*texts.values(), *catalogs]
    apps = [t for p, t in texts.items() if p.name.startswith("build.gradle") and APPLICATION.search(t)]
    out = {}
    for key in ("minSdk", "targetSdk"):
        values = set()
        for text in apps:
            expr = _value_expr(_block(text), key)
            values.add(_resolve(expr, every) if expr else None)
        out[key] = values.pop() if len(values) == 1 else None
    return out
