"""harness.yaml for cryptobenchmark: each applied scope's original and patched function, extracted verbatim."""
from __future__ import annotations

import shutil
from pathlib import Path

from ..dto.site import METRICS, SCHEMA_VERSION, Replacement, Scope
from ..files import write_text
from .dependencies import dependencies, load
from ..run_dir import AppPaths
from .edit import function_lines, import_lines, language, read_source


def _extract(out: AppPaths, scope: Scope, side: str, text: str) -> str:
    path = out.extracts / scope.id / f"{side}{Path(scope.file).suffix}"
    path.parent.mkdir(parents=True, exist_ok=True)
    write_text(path, function_lines(text, scope.start, scope.end))
    return str(path.relative_to(out.root))


def harness(out: AppPaths, scopes: dict[str, Scope], replacements: dict[str, Replacement], edits: dict,
            currents: dict[str, str]) -> dict:
    """Paths in the document are relative to harness.yaml's folder; `currents` is each dossier's current item."""
    shutil.rmtree(out.extracts, ignore_errors=True)
    entries = []
    for row in sorted((e for e in edits["edits"] if e["status"] == "applied"), key=lambda e: e["scope"]):
        scope = scopes[row["scope"]]
        lang = language(scope.file)
        original = read_source(out.original / scope.file)
        patched = read_source(out.patched / scope.file)
        imports = import_lines(original, lang)
        names = load(lang.name)
        uses = set()
        for text in (original, patched):
            uses |= set(dependencies(function_lines(text, scope.start, scope.end), lang, imports, names))
        entries.append({
            "id": scope.id,
            "language": lang.name,
            "function": scope.function,
            "before": _extract(out, scope, "before", original),
            "after": _extract(out, scope, "after", patched),
            "imports": imports,
            "inputs": {"inputSize": scope.inputSize, "keySize": scope.keySize},
            "current": currents[scope.id],
            "option": replacements[scope.id].option,
            "metrics": list(METRICS),
            "dependencies": sorted(uses),
        })
    return {"schemaVersion": SCHEMA_VERSION, "app": out.app, "scopes": entries}
