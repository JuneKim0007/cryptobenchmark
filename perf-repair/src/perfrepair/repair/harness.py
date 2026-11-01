"""harness.yaml for cryptobenchmark: each applied scope's original and patched function, extracted verbatim."""
from __future__ import annotations

import shutil
from pathlib import Path

from ..dto.site import METRICS, SCHEMA_VERSION, Replacement, Scope
from ..files import write_text
from .dependencies import dependencies, load
from .edit.app import read_source
from .edit.lexer import lex
from .edit.locate import line_offsets
from .edit.plan import language
from .paths import AppPaths


def function_lines(text: str, start: int, end: int) -> str:
    """Lines `start..end`, 1-based inclusive; edits keep line numbers, so one range serves both copies."""
    starts = line_offsets(text)
    return text[starts[start - 1]:starts[end] if end < len(starts) else len(text)]


def import_lines(text: str) -> list[str]:
    masked = lex(text).masked.splitlines()
    return [line.strip() for line, code in zip(text.splitlines(), masked) if code.lstrip().startswith("import ")]


def _extract(out: AppPaths, scope: Scope, side: str, text: str) -> str:
    path = out.extracts / scope.id / f"{side}{Path(scope.file).suffix}"
    path.parent.mkdir(parents=True, exist_ok=True)
    write_text(path, function_lines(text, scope.start, scope.end))
    return str(path.relative_to(out.root))


def harness(out: AppPaths, scopes: dict[str, Scope], replacements: dict[str, Replacement], edits: dict) -> dict:
    """Paths in the document are relative to harness.yaml's folder."""
    shutil.rmtree(out.extracts, ignore_errors=True)
    entries = []
    for row in sorted((e for e in edits["edits"] if e["status"] == "applied"), key=lambda e: e["scope"]):
        scope = scopes[row["scope"]]
        lang = language(scope.file)
        original = read_source(out.original / scope.file)
        patched = read_source(out.patched / scope.file)
        imports = import_lines(original)
        names = load(lang)
        uses = set()
        for text in (original, patched):
            uses |= set(dependencies(function_lines(text, scope.start, scope.end), lang, imports, names))
        entries.append({
            "id": scope.id,
            "language": lang,
            "function": scope.function,
            "before": _extract(out, scope, "before", original),
            "after": _extract(out, scope, "after", patched),
            "imports": imports,
            "inputs": {"inputSize": scope.inputSize, "keySize": scope.keySize},
            "option": replacements[scope.id].option,
            "metrics": list(METRICS),
            "dependencies": sorted(uses),
        })
    return {"schemaVersion": SCHEMA_VERSION, "app": out.app, "scopes": entries}
