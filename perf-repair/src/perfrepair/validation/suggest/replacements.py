"""replacements: each one names a known scope, a well-formed decision, and edits that apply its option exactly."""
from __future__ import annotations

from ...dto.site import DECISIONS, EDIT_FIELDS, EDIT_KIND_TABLE, EDIT_KINDS, RISKS, Dossier, Replacement, required_risks
from .replace import required_kinds, takes

SOURCES = ("llm", "fallback", "static")


def _edits(r: Replacement, d: Dossier) -> list[str]:
    option = next((o for o in d.options if o.item == r.option), None)
    if option is None:
        return [f"{r.scope}: option {r.option!r} is not an option of its dossier"]
    if option.pins is None:
        return [f"{r.scope}: option {option.alias} has unknown pins and cannot be a replace"]
    kinds = [e.kind for e in r.edits]
    problems = []
    if not kinds or len(set(kinds)) != len(kinds) or set(kinds) - set(EDIT_KINDS):
        problems.append(f"{r.scope}: edit kinds {kinds} are not distinct kinds of {EDIT_KINDS}")
    for e in (e for e in r.edits if e.kind in EDIT_KIND_TABLE):
        row = EDIT_KIND_TABLE[e.kind]
        if (getattr(e, row.field) != takes(e.kind, option.item, option.pins)
                or any(getattr(e, f) for f in EDIT_FIELDS if f != row.field)):
            problems.append(f"{r.scope}: {e.kind} is not exactly the option's {row.takes}")
    problems += [f"{r.scope}: the option's {EDIT_KIND_TABLE[k].takes} needs {k}, which is not applied"
                 for k in required_kinds(option, d.current) if k not in kinds]
    problems += [f"{r.scope}: risk {k} implied by the scope is not declared" for k in required_risks(d.scope)
                 if k not in r.risks]
    return problems


def _static(k: str, r: Replacement, source: str | None, no_options: dict[str, str]) -> list[str]:
    if (source == "static") != (k in no_options):
        return [f"{k}: static is the source exactly of the noOptions scopes"]
    if k in no_options and (r.decision != "keep" or r.reason != no_options[k]):
        return [f"{k}: a noOptions scope is a keep whose reason is its code {no_options[k]!r}"]
    return []


def validate_replacements(replacements: dict[str, Replacement], sources: dict[str, str],
                          dossiers: list[Dossier], no_options: dict[str, str]) -> list[str]:
    by_key = {d.key: d for d in dossiers}
    problems = [f"{k}: replacement for an unknown scope" for k in replacements if k not in by_key and k not in no_options]
    problems += [f"{k}: noOptions scope without its static keep" for k in no_options if k not in replacements]
    problems += [f"{k}: source {sources.get(k)!r} is not one of {SOURCES}" for k in replacements
                 if sources.get(k) not in SOURCES]
    problems += [f"{k}: source without a replacement" for k in sources if k not in replacements]
    for k, r in replacements.items():
        problems += [p for p in (
            f"{k}: filed under {k} but names scope {r.scope}" if r.scope != k else "",
            f"{k}: decision {r.decision!r} is not one of {DECISIONS}" if r.decision not in DECISIONS else "",
            f"{k}: keep carries an option or edits" if r.decision == "keep" and (r.option or r.edits) else "",
            f"{k}: risks {list(r.risks)} outside {RISKS}" if set(r.risks) - set(RISKS) else "",
            f"{k}: reason is empty" if not r.reason.strip() else "",
            f"{k}: a fallback is not a keep" if sources.get(k) == "fallback" and r.decision != "keep" else "",
        ) if p]
        problems += _static(k, r, sources.get(k), no_options)
        if r.decision == "replace" and k in by_key:
            problems += _edits(r, by_key[k])
    return problems
