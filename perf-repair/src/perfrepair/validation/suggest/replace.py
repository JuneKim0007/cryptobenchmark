"""Gate C of the replacement decision: a reply against its dossier, in the aliases the model saw."""
from __future__ import annotations

import json

from ...dto.site import DECISIONS, EDIT_KINDS, Dossier, Edit, Option, Replacement
from ..json_reply import parse_object
from .dossier import provider_of

RISKS = ("persisted_data", "wire_format", "key_compatibility", "unknown_sink")


def pin_text(value) -> str:
    return value if isinstance(value, str) else json.dumps(value)


def _text(d: dict, field: str) -> str | None:
    return d.get(field) if isinstance(d.get(field), str) else None


def _parameters(raw, where: str, problems: list[str]) -> dict[str, str]:
    if not isinstance(raw, list):
        problems.append(f"{where}: parameters is not a list")
        return {}
    out = {}
    for j, p in enumerate(raw):
        if not isinstance(p, dict) or _text(p, "name") is None or _text(p, "value") is None:
            problems.append(f"{where}: parameters[{j}] is not a {{name, value}} pair of strings")
        elif p["name"] in out:
            problems.append(f"{where}: parameter {p['name']!r} given twice")
        else:
            out[p["name"]] = p["value"]
    return out


def _pins(given: dict[str, str], option: Option, where: str) -> list[str]:
    want = {k: pin_text(v) for k, v in option.pins.items()}
    if not want:
        return [f"{where}: pin_parameters on {option.alias}, which lists no pins"]
    problems = [f"{where}: pin {k!r} of {option.alias} is missing" for k in want if k not in given]
    problems += [f"{where}: {k!r} is not a pin of {option.alias} ({', '.join(want)})" for k in given if k not in want]
    problems += [f"{where}: pin {k!r} is {given[k]!r}, but {option.alias} lists {want[k]!r}"
                 for k in want if k in given and given[k] != want[k]]
    return problems


def _edits(raw: list, option: Option | None, current: str, problems: list[str]) -> list[Edit]:
    edits, kinds = [], []
    for i, e in enumerate(raw):
        where = f"edits[{i}]"
        if not isinstance(e, dict):
            problems.append(f"{where} is not an object")
            continue
        kind, provider = e.get("kind"), _text(e, "provider")
        if kind not in EDIT_KINDS:
            problems.append(f"{where}: kind {kind!r} is not one of {EDIT_KINDS}")
            continue
        if kind in kinds:
            problems.append(f"{where}: {kind} given more than once")
        kinds.append(kind)
        given = _parameters(e.get("parameters"), where, problems)
        if provider is None:
            problems.append(f"{where}: provider is not a string")
        if option is None:
            continue
        if kind == "set_provider":
            if provider is not None and provider != provider_of(option.item):
                problems.append(f"{where}: set_provider names {provider!r}, but {option.alias} is provided by "
                                f"{provider_of(option.item)!r}")
            if given:
                problems.append(f"{where}: set_provider takes no parameters")
            edits.append(Edit(kind, provider=provider_of(option.item)))
        else:
            if provider:
                problems.append(f"{where}: pin_parameters takes no provider")
            problems += _pins(given, option, where)
            edits.append(Edit(kind, parameters=dict(option.pins)))
    if option is not None:
        if option.pins and "pin_parameters" not in kinds:
            problems.append(f"{option.alias} lists pins; pin_parameters must state them")
        if provider_of(option.item) != provider_of(current) and "set_provider" not in kinds:
            problems.append(f"{option.alias} is provided by {provider_of(option.item)!r}, not the current "
                            f"{provider_of(current)!r}; set_provider must name it")
    return edits


def check_reply(text: str, dossier: Dossier) -> tuple[dict | None, list[str]]:
    d, problems = parse_object(text)
    if d is None:
        return None, problems
    decision, alias, reason = d.get("decision"), _text(d, "option"), (_text(d, "reason") or "").strip()
    edits = d.get("edits") if isinstance(d.get("edits"), list) else None
    risks = d.get("risks") if isinstance(d.get("risks"), list) else None
    by_alias = {o.alias: o for o in dossier.options}
    problems = [p for p in (
        f"decision {decision!r} is not one of {DECISIONS}" if decision not in DECISIONS else "",
        "option is not a string" if alias is None else "",
        "edits is not a list" if edits is None else "",
        "risks is not a list" if risks is None else "",
        "reason is empty" if not reason else "",
    ) if p]
    edits, risks = edits or [], risks or []
    option = None
    if decision == "replace":
        if alias not in by_alias:
            problems.append(f"option {alias!r} is not one of {', '.join(by_alias) or '(none)'}")
        else:
            option = by_alias[alias]
        if not edits:
            problems.append("replace names no edit")
    if decision == "keep":
        if alias:
            problems.append(f"keep names option {alias!r}; a keep has none")
        if edits:
            problems.append("keep names edits; a keep has none")
    resolved = _edits(edits, option, dossier.current, problems)
    problems += [f"risk {r!r} is not one of {RISKS}" for r in risks if r not in RISKS]
    problems += [f"risk {r!r} given more than once" for r in sorted({r for r in risks if isinstance(r, str)
                                                                       and risks.count(r) > 1})]
    if problems:
        return None, problems
    return Replacement(dossier.key, decision, option.item if option else None, tuple(resolved), tuple(risks),
                       reason).to_json(), []
