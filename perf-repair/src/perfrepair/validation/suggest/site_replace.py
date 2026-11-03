"""Gate C of the replacement decision: a reply against its unit, in the aliases the model saw: every member given an
option of its own, or the unit kept."""
from __future__ import annotations

from ...dto.grouping import algorithm_of, provider_of
from ...dto.site import (DECISIONS, EDIT_FIELDS, EDIT_KIND_TABLE, EDIT_KINDS, RISKS, Dossier, Edit, Option,
                         Replacement, Scope, pin_text, required_risks)
from ...dto.unit import UnitDossiers
from ..json_reply import parse_object


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


_TAKES = {"provider": lambda item, pins: provider_of(item), "algorithm": lambda item, pins: algorithm_of(item),
          "pins": lambda item, pins: dict(pins)}


def takes(kind: str, item: str, pins: dict):
    """What `kind` fills its field with for an item and its pins; the current call has no pins."""
    return _TAKES[EDIT_KIND_TABLE[kind].takes](item, pins)


def _pins(kind: str, given: dict[str, str], want: dict, option: Option, where: str) -> list[str]:
    want = {k: pin_text(v) for k, v in want.items()}
    if not want:
        return [f"{where}: {kind} on {option.alias}, which lists no pins"]
    problems = [f"{where}: pin {k!r} of {option.alias} is missing" for k in want if k not in given]
    problems += [f"{where}: {k!r} is not a pin of {option.alias} ({', '.join(want)})" for k in given if k not in want]
    problems += [f"{where}: pin {k!r} is {given[k]!r}, but {option.alias} lists {want[k]!r}"
                 for k in want if k in given and given[k] != want[k]]
    return problems


def _named(kind: str, given: str | None, want: str, option: Option, where: str) -> list[str]:
    if given is not None and given != want:
        return [f"{where}: {kind} names {given!r}, but {option.alias} {EDIT_KIND_TABLE[kind].phrase} {want!r}"]
    return []


def _missing_named(kind: str, want: str, current: str, option: Option) -> str:
    return f"{option.alias} {EDIT_KIND_TABLE[kind].phrase} {want!r}, not the current {current!r}; {kind} must name it"


def _missing_pins(kind: str, want: dict, current: dict, option: Option) -> str:
    row = EDIT_KIND_TABLE[kind]
    return f"{option.alias} {row.phrase} {row.takes}; {kind} must state them"


# by the Edit field a kind fills: how a given value is checked, and the words when the kind is missing
_CHECK = {"provider": _named, "algorithm": _named, "parameters": _pins}
_MISSING = {"provider": _missing_named, "algorithm": _missing_named, "parameters": _missing_pins}


def _resolve(kind: str, e: dict, option: Option, where: str, problems: list[str]) -> Edit:
    field = EDIT_KIND_TABLE[kind].field
    values = {"provider": _text(e, "provider"), "algorithm": _text(e, "algorithm"),
              "parameters": _parameters(e.get("parameters"), where, problems)}
    problems += [f"{where}: {kind} takes no {f}" for f in EDIT_FIELDS if f != field and values[f]]
    want = takes(kind, option.item, option.pins)
    problems += _CHECK[field](kind, values[field], want, option, where)
    return Edit(kind, **{field: want})


def required_kinds(option: Option, current: str) -> list[str]:
    """The kinds whose value for the option differs from the current call's."""
    return [k for k in EDIT_KINDS if takes(k, option.item, option.pins) != takes(k, current, {})]


def _edits(raw: list, option: Option | None, current: str, problems: list[str]) -> list[Edit]:
    edits, kinds = [], []
    for i, e in enumerate(raw):
        where = f"edits[{i}]"
        if not isinstance(e, dict):
            problems.append(f"{where} is not an object")
            continue
        kind = e.get("kind")
        if kind not in EDIT_KINDS:
            problems.append(f"{where}: kind {kind!r} is not one of {EDIT_KINDS}")
            continue
        if kind in kinds:
            problems.append(f"{where}: {kind} given more than once")
        kinds.append(kind)
        problems += [f"{where}: {f} is not a string" for f in ("provider", "algorithm") if _text(e, f) is None]
        if option is not None:
            edits.append(_resolve(kind, e, option, where, problems))
    if option is not None:
        for kind in required_kinds(option, current):
            if kind not in kinds:
                want, have = takes(kind, option.item, option.pins), takes(kind, current, {})
                problems.append(_MISSING[EDIT_KIND_TABLE[kind].field](kind, want, have, option))
    return edits


def _risks(risks: list, scope: Scope, option: Option | None, decision: str) -> list[str]:
    problems = [f"risk {r!r} is not one of {RISKS}" for r in risks if r not in RISKS]
    problems += [f"risk {r!r} given more than once" for r in sorted({r for r in risks if isinstance(r, str)
                                                                       and risks.count(r) > 1})]
    if decision == "replace":
        problems += [f"risks must include {r}: {' and '.join(words)}"
                     for r, words in required_risks(scope, option).items() if r not in risks]
    return problems


def _replace_member(raw: dict, alias: str, dossier: Dossier, reason: str, problems: list[str]) -> dict | None:
    """One member's option, edits and risks against its own dossier; its problems name the member."""
    found: list[str] = []
    chosen, edits, risks = _text(raw, "option"), raw.get("edits"), raw.get("risks")
    by_alias = {o.alias: o for o in dossier.options}
    found += ["edits is not a list"] * (not isinstance(edits, list)) + ["risks is not a list"] * (not isinstance(risks, list))
    edits, risks = edits if isinstance(edits, list) else [], risks if isinstance(risks, list) else []
    option = None
    if chosen not in by_alias:
        found.append(f"option {chosen!r} is not one of {', '.join(by_alias) or '(none)'}")
    elif by_alias[chosen].pins is None:
        found.append(f"{chosen} has unknown pins, so no like-for-like swap can be stated; it cannot be chosen")
    else:
        option = by_alias[chosen]
    if not edits:
        found.append("replace names no edit")
    resolved = _edits(edits, option, dossier.current, found)
    found += _risks(risks, dossier.scope, option, "replace")
    problems += [f"{alias}: {p}" for p in found]
    if found:
        return None
    return Replacement(dossier.key, "replace", option.item, tuple(resolved), tuple(risks), reason).to_json()


def _members(raw: list, unit: UnitDossiers, reason: str, problems: list[str]) -> list[dict]:
    aliased = unit.aliased()
    given = [m.get("member") if isinstance(m, dict) else None for m in raw]
    problems += [f"member {a!r} is not one of {', '.join(aliased)}" for a in given if a not in aliased]
    problems += [f"member {a} given more than once" for a in aliased if given.count(a) > 1]
    problems += [f"a unit is replaced whole: member {a} has no option" for a in aliased if a not in given]
    rows = []
    for alias, m in zip(given, raw):
        if alias in aliased and given.count(alias) == 1:
            rows.append(_replace_member(m, alias, aliased[alias], reason, problems))
    return rows


def check_reply(text: str, unit: UnitDossiers) -> tuple[dict | None, list[str]]:
    d, problems = parse_object(text)
    if d is None:
        return None, problems
    decision, members, reason = d.get("decision"), d.get("members"), (_text(d, "reason") or "").strip()
    problems = [p for p in (
        f"decision {decision!r} is not one of {DECISIONS}" if decision not in DECISIONS else "",
        "members is not a list" if not isinstance(members, list) else "",
        "reason is empty" if not reason else "",
    ) if p]
    members = members if isinstance(members, list) else []
    rows: list = []
    if decision == "keep" and members:
        problems.append("keep names members; a keep covers the whole unit and has none")
    if decision == "replace":
        rows = _members(members, unit, reason, problems)
    if problems:
        return None, problems
    if decision == "keep":
        rows = [Replacement(m, "keep", None, (), (), reason).to_json() for m in unit.unit.members]
    return {"replacements": rows}, []
