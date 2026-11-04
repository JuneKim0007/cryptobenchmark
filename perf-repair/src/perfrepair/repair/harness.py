"""harness.yaml for cryptobenchmark: each applied scope's original and patched function, extracted verbatim, its needed imports."""
from __future__ import annotations

import shutil
from pathlib import Path

from ..dto.site import HARNESS_SCHEMA_VERSION, METRICS, NO_OPERATION, Scope
from ..dto.replacement import Replacement
from ..dto.unit import Unit, units_by_scope
from ..files import write_text_making_parents
from ..source.lexer import Code
from .dependencies import dependencies, load
from ..run_dir import AppPaths
from .edit import function_lines, import_lines, language, read_source
from .imports import used_imports
from .inputs import scope_inputs
from .inverses import inverse_partners
from .operation import has_operation


def _extract(out: AppPaths, scope: Scope, side: str, text: str) -> str:
    path = out.extracts / scope.id / f"{side}{Path(scope.file).suffix}"
    write_text_making_parents(path, function_lines(text, scope.start, scope.end))
    return str(path.relative_to(out.root))


def harness(out: AppPaths, scopes: dict[str, Scope], replacements: dict[str, Replacement], edits: dict,
            currents: dict[str, str], effective: dict, units: list[Unit]) -> dict:
    """Paths in the document are relative to harness.yaml's folder; `currents` is each dossier's current item."""
    shutil.rmtree(out.extracts, ignore_errors=True)
    entries = []
    applied = sorted((e for e in edits["edits"] if e["status"] == "applied"), key=lambda e: e["scope"])
    inverses, of_unit = inverse_partners(units, {e["scope"] for e in applied}), units_by_scope(units)
    for row in applied:
        scope = scopes[row["scope"]]
        lang = language(scope.file)
        original = read_source(out.original / scope.file)
        alone = out.alone(of_unit[scope.id].id) / scope.file
        patched = read_source(alone if alone.is_file() else out.patched / scope.file)
        imports = import_lines(original, lang)
        names = load(lang.name)
        functions = [function_lines(text, scope.start, scope.end) for text in (original, patched)]
        uses = sorted({name for f in functions for name in dependencies(f, lang, imports, names)})
        entries.append({
            "id": scope.id,
            "language": lang.name,
            "function": scope.function,
            "before": _extract(out, scope, "before", original),
            "after": _extract(out, scope, "after", patched),
            "imports": used_imports(imports, functions, lang, names, uses),
            "inputs": scope_inputs(scope, currents[scope.id], replacements[scope.id].option, effective),
            "current": currents[scope.id],
            "option": replacements[scope.id].option,
            "metrics": list(METRICS),
            "dependencies": uses,
            "notMeasurable": None if has_operation(Code.of(original, lang), scope) else NO_OPERATION,
            "inverse": inverses.get(scope.id),
        })
    return {"schemaVersion": HARNESS_SCHEMA_VERSION, "app": out.app, "scopes": entries}
