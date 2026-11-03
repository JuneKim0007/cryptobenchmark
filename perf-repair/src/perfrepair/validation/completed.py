"""completed.json against gaps.json, and each model completion in scopes.json against the answer it came from."""
from __future__ import annotations

from ..dto.gaps import UNKNOWN_CHOICE, USE_GAP, Answer, ScopeGaps
from ..dto.lifecycle import MODEL_PREFIX, Lifecycle


def validate_completed(answers: dict[str, tuple[Answer, ...]], entries: list[ScopeGaps]) -> list[str]:
    known, out = {e.key: e for e in entries}, []
    for scope, rows in answers.items():
        entry = known.get(scope)
        if entry is None:
            out.append(f"completed: scope {scope} is not in gaps.json")
            continue
        missing = {g.id for g in entry.offered} - {a.gap for a in rows}
        extra = {a.gap for a in rows} - {g.id for g in entry.offered}
        out += [f"completed {scope}: gap {g} has no answer" for g in sorted(missing)]
        out += [f"completed {scope}: gap {g} was not offered" for g in sorted(extra)]
    return out


def _expected(entry: ScopeGaps, rows: tuple[Answer, ...]) -> dict[tuple, tuple]:
    offered = {g.id: g for g in entry.offered}
    out = {}
    for a in (a for a in rows if a.choice != UNKNOWN_CHOICE and a.gap in offered):
        line = next((c for c in offered[a.gap].candidates if c.id == a.choice), None)
        if line is not None:
            out[offered[a.gap].requirement] = (a.origin, line.line, line.file)
    return out


def _found(lc: Lifecycle, fingerprint: str, where: str) -> tuple[dict[tuple, tuple], list[str]]:
    found, out = {}, []
    held = [(r.key, r.completed) for r in lc.requirements if r.completed is not None]
    held += [((USE_GAP,), lc.use)] if lc.use is not None else []
    for key, done in held:
        if done.by_model:
            found[key] = (done.origin, done.line, done.file)
            if done.source != f"{MODEL_PREFIX}{fingerprint}":
                out.append(f"{where}: completion source {done.source} is not the active outbox {fingerprint}")
    return found, out


def _scope_problems(s: dict, entry: ScopeGaps | None, rows: tuple[Answer, ...], fingerprint: str) -> list[str]:
    found, out = _found(Lifecycle.from_json(s["lifecycle"]), fingerprint, f"scopes {s['id']}")
    expected = _expected(entry, rows) if entry is not None else {}
    expected = {(k if k[0] != USE_GAP else (USE_GAP,)): v for k, v in expected.items()}
    out += [f"scopes {s['id']}: completion {k} equals no answer" for k, v in found.items() if expected.get(k) != v]
    return out + [f"scopes {s['id']}: answer {k} is not applied" for k in expected if found and k not in found]


def validate_completions(scopes_doc: dict, answers: dict[str, tuple[Answer, ...]], entries: list[ScopeGaps],
                         fingerprint: str) -> list[str]:
    """Every model completion comes from an answer; when the scope holds any, every chosen answer is there."""
    known = {e.key: e for e in entries}
    return [p for s in scopes_doc["scopes"] if s.get("lifecycle") is not None
            for p in _scope_problems(s, known.get(s["id"]), answers.get(s["id"], ()), fingerprint)]
