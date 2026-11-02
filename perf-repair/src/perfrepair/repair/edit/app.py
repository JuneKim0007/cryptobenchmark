"""An app's `replace` decisions applied to copies: `original/` and `patched/` of each changed file, and edits.json."""
from __future__ import annotations

import shutil
from pathlib import Path

from ...dto.site import SCHEMA_VERSION, Replacement, Scope
from ...files import write_text
from ...run_dir import AppPaths
from ...source.lexer import Code
from .plan import language, plan
from .reject import Rejected
from .specs import Table
from .splice import Splice, apply, diff


def _source_file(root: Path, file: str) -> Path:
    path = (root / file).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"{file}: outside the app root")
    return path


def read_source(path: Path) -> str:
    with path.open(encoding="utf-8", newline="") as f:
        return f.read()


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    write_text(path, text)


def edit_app(scopes: dict[str, Scope], replacements: list[Replacement], root: Path, out: AppPaths,
             table: Table) -> dict:
    sources: dict[str, Code] = {}
    accepted: dict[str, list[Splice]] = {}
    rows = []
    for r in sorted((r for r in replacements if r.decision == "replace"), key=lambda r: r.scope):
        if r.scope not in scopes:
            raise ValueError(f"{r.scope}: replacement for a scope missing from scopes.json")
        if any(row["scope"] == r.scope for row in rows):
            raise ValueError(f"{r.scope}: two replacements for one scope")
        scope = scopes[r.scope]
        if scope.app != out.app:
            raise ValueError(f"{r.scope}: scope of app {scope.app!r}, not {out.app!r}")
        try:
            path = _source_file(root, scope.file)
            if not path.is_file():
                raise Rejected("file_missing")
            if scope.file not in sources:
                sources[scope.file] = Code.of(read_source(path), language(scope.file))
            source = sources[scope.file]
            splices = plan(scope, r, source, table)
            apply(source.text, accepted.get(scope.file, []) + splices)
        except Rejected as e:
            rows.append({"scope": r.scope, "status": "rejected", "reason": e.reason, "diff": ""})
            continue
        accepted.setdefault(scope.file, []).extend(splices)
        rows.append({"scope": r.scope, "status": "applied", "reason": None,
                     "diff": diff(scope.file, source.text, apply(source.text, splices))})
    for directory in (out.original, out.patched):
        shutil.rmtree(directory, ignore_errors=True)
    for file, splices in sorted(accepted.items()):
        _write(out.original / file, sources[file].text)
        _write(out.patched / file, apply(sources[file].text, splices))
    return {"schemaVersion": SCHEMA_VERSION, "app": out.app, "edits": rows}
