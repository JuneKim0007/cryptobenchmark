"""replacements: each one names a known scope, a well-formed decision, and edits that apply its option exactly."""
from __future__ import annotations

from ...dto.site import DECISIONS, EDIT_KINDS, Dossier, Replacement
from .dossier import provider_of
from .replace import RISKS

SOURCES = ("llm", "fallback", "static")


def _edits(r: Replacement, d: Dossier) -> list[str]:
    option = next((o for o in d.options if o.item == r.option), None)
    if option is None:
        return [f"{r.scope}: option {r.option!r} is not an option of its dossier"]
    kinds = [e.kind for e in r.edits]
    problems = []
    if not kinds or len(set(kinds)) != len(kinds) or set(kinds) - set(EDIT_KINDS):
        problems.append(f"{r.scope}: edit kinds {kinds} are not distinct kinds of {EDIT_KINDS}")
    for e in r.edits:
        if e.kind == "set_provider" and (e.provider != provider_of(option.item) or e.parameters):
            problems.append(f"{r.scope}: set_provider is not exactly the option's provider")
        if e.kind == "pin_parameters" and (e.parameters != option.pins or e.provider):
            problems.append(f"{r.scope}: pin_parameters is not exactly the option's pins")
    if option.pins and "pin_parameters" not in kinds:
        problems.append(f"{r.scope}: the option's pins are not applied")
    return problems


def validate_replacements(replacements: dict[str, Replacement], sources: dict[str, str],
                          dossiers: list[Dossier]) -> list[str]:
    by_key = {d.key: d for d in dossiers}
    problems = [f"{k}: replacement for an unknown scope" for k in replacements if k not in by_key]
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
        if r.decision == "replace" and k in by_key:
            problems += _edits(r, by_key[k])
    return problems
