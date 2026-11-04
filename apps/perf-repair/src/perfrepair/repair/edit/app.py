"""An app's `replace` decisions applied to copies, atomically over each unit's replaced members (a member that stays has
no edit): `original/` and `patched/` of each changed file, and edits.json."""
from __future__ import annotations

import shutil
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from ...dto.replacement import Replacement
from ...dto.site import EDITS_SCHEMA_VERSION, Scope
from ...dto.unit import Unit, units_by_scope
from ...files import write_text_making_parents
from ...run_dir import AppPaths
from ...source.code import Code
from .alone import write_alone
from .plan import language, plan
from .reject import Rejected
from .specs import Table
from .splice import Splice, apply, diff

UNIT_MEMBER_REJECTED = "unit_member_rejected"


def _source_file(root: Path, file: str) -> Path:
    path = (root / file).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"{file}: outside the app root")
    return path


def read_source(path: Path) -> str:
    with path.open(encoding="utf-8", newline="") as f:
        return f.read()


def _refused(replacements: list[Replacement], scopes: dict[str, Scope], app: str) -> None:
    seen = set()
    for r in replacements:
        if r.scope not in scopes:
            raise ValueError(f"{r.scope}: replacement for a scope missing from scopes.json")
        if r.scope in seen:
            raise ValueError(f"{r.scope}: two replacements for one scope")
        seen.add(r.scope)
        if scopes[r.scope].app != app:
            raise ValueError(f"{r.scope}: scope of app {scopes[r.scope].app!r}, not {app!r}")


@dataclass
class _Run:
    scopes: dict[str, Scope]
    root: Path
    table: Table
    sources: dict[str, Code] = field(default_factory=dict)
    accepted: dict[str, list[Splice]] = field(default_factory=dict)
    by_unit: dict[str, dict[str, list[Splice]]] = field(default_factory=dict)

    def _splices(self, r: Replacement, planned: dict[str, list[Splice]]) -> list[Splice]:
        scope = self.scopes[r.scope]
        path = _source_file(self.root, scope.file)
        if not path.is_file():
            raise Rejected("file_missing")
        if scope.file not in self.sources:
            self.sources[scope.file] = Code.of(read_source(path), language(scope.file))
        source = self.sources[scope.file]
        splices = plan(scope, r, source, self.table)
        apply(source.text, self.accepted.get(scope.file, []) + planned[scope.file] + splices)
        return splices

    def unit(self, uid: str, members: list[Replacement]) -> list[dict]:
        """Every replaced member applied, or none: one rejection rejects them all, and the other rows name it."""
        planned: dict[str, list[Splice]] = defaultdict(list)
        own, rejected = {}, {}
        for r in members:
            try:
                own[r.scope] = self._splices(r, planned)
                planned[self.scopes[r.scope].file] += own[r.scope]
            except Rejected as e:
                rejected[r.scope] = e.reason
        if rejected:
            return [_rejected(r.scope, rejected) for r in members]
        for file, splices in planned.items():
            self.accepted.setdefault(file, []).extend(splices)
        self.by_unit[uid] = dict(planned)
        return [self._applied(r.scope, own[r.scope]) for r in members]

    def _applied(self, scope_id: str, splices: list[Splice]) -> dict:
        file = self.scopes[scope_id].file
        text = self.sources[file].text
        return {"scope": scope_id, "status": "applied", "reason": None, "diff": diff(file, text, apply(text, splices))}


def _rejected(scope_id: str, rejected: dict[str, str]) -> dict:
    if scope_id in rejected:
        return {"scope": scope_id, "status": "rejected", "reason": rejected[scope_id], "diff": ""}
    first = min(rejected)
    return {"scope": scope_id, "status": "rejected", "reason": UNIT_MEMBER_REJECTED, "diff": "",
            "blockedBy": f"{first}: {rejected[first]}"}


def edit_app(scopes: dict[str, Scope], replacements: list[Replacement], root: Path, out: AppPaths,
             table: Table, units: list[Unit]) -> dict:
    chosen = sorted((r for r in replacements if r.decision == "replace"), key=lambda r: r.scope)
    _refused(chosen, scopes, out.app)
    of_unit = units_by_scope(units)
    grouped: dict[str, list[Replacement]] = defaultdict(list)
    for r in chosen:
        if r.scope not in of_unit:
            raise ValueError(f"{r.scope}: scope in no unit of units.json")
        grouped[of_unit[r.scope].id].append(r)
    run = _Run(scopes, root, table)
    rows = [row for uid in sorted(grouped, key=lambda uid: grouped[uid][0].scope) for row in run.unit(uid, grouped[uid])]
    for directory in (out.original, out.patched):
        shutil.rmtree(directory, ignore_errors=True)
    for file, splices in sorted(run.accepted.items()):
        write_text_making_parents(out.original / file, run.sources[file].text)
        write_text_making_parents(out.patched / file, apply(run.sources[file].text, splices))
    write_alone(run.by_unit, units, scopes, {file: code.text for file, code in run.sources.items()}, out)
    return {"schemaVersion": EDITS_SCHEMA_VERSION, "app": out.app, "edits": sorted(rows, key=lambda row: row["scope"])}
