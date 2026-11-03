"""Gate C of the replacement decision: a reply against its unit, in the aliases the model saw: every member with options
given an option of its own, or all of them kept; a member that stays is never named; an inverse pair left on two items
needs their interop."""
from __future__ import annotations

from ...dto.change import DROP_IN, SAME, admits
from ...dto.grouping import algorithm_of, provider_of
from ...dto.site import (DECISIONS, EDIT_FIELDS, EDIT_KIND_TABLE, EDIT_KINDS, RISKS, Dossier, Edit, Option,
                         Replacement, Scope, pin_text, required_risks)
from ...dto.unit import INVERSE, Link, UnitDossiers
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


def _chosen(chosen: str | None, by_alias: dict[str, Option], max_change: str, found: list[str]) -> Option | None:
    if chosen not in by_alias:
        found.append(f"option {chosen!r} is not one of {', '.join(by_alias) or '(none)'}")
    elif not admits(max_change, by_alias[chosen].change):
        found.append(f"{chosen} is a {by_alias[chosen].change}, above maxChange {max_change}; it cannot be chosen")
    elif by_alias[chosen].pins is None:
        found.append(f"{chosen} has unknown pins, so no like-for-like swap can be stated; it cannot be chosen")
    else:
        return by_alias[chosen]
    return None


def _replace_member(raw: dict, alias: str, dossier: Dossier, reason: str, problems: list[str],
                    max_change: str = DROP_IN) -> dict | None:
    """One member's option, edits and risks against its own dossier; its problems name the member."""
    found: list[str] = []
    chosen, edits, risks = _text(raw, "option"), raw.get("edits"), raw.get("risks")
    by_alias = {o.alias: o for o in dossier.options}
    found += ["edits is not a list"] * (not isinstance(edits, list)) + ["risks is not a list"] * (not isinstance(risks, list))
    edits, risks = edits if isinstance(edits, list) else [], risks if isinstance(risks, list) else []
    option = _chosen(chosen, by_alias, max_change, found)
    if not edits:
        found.append("replace names no edit")
    resolved = _edits(edits, option, dossier.current, found)
    found += _risks(risks, dossier.scope, option, "replace")
    problems += [f"{alias}: {p}" for p in found]
    if found:
        return None
    return Replacement(dossier.key, "replace", option.item, tuple(resolved), tuple(risks), reason).to_json()


def _staying(given: list, unit: UnitDossiers) -> list[str]:
    stayed = unit.stayed()
    return [f"member {a} has no option; it stays on {stayed[a].current or 'what it uses'}" for a in given if a in stayed]


def _named(given: list, unit: UnitDossiers) -> list[str]:
    aliased, problems = unit.aliased(), _staying(given, unit)
    problems += [f"member {a!r} is not one of {', '.join(aliased)}" for a in given if a not in aliased and a not in unit.stayed()]
    problems += [f"member {a} given more than once" for a in aliased if given.count(a) > 1]
    return problems + [f"replace covers every member with options: {a} is missing" for a in aliased if a not in given]


def _members(raw: list, unit: UnitDossiers, reason: str, problems: list[str], max_change: str) -> list[dict]:
    aliased = unit.aliased()
    given = [m.get("member") if isinstance(m, dict) else None for m in raw]
    problems += _named(given, unit)
    rows = []
    for alias, m in zip(given, raw):
        if alias in aliased and given.count(alias) == 1:
            rows.append(_replace_member(m, alias, aliased[alias], reason, problems, max_change))
    problems += [] if problems else _inverse(unit, rows)
    return rows


def _inverse(unit: UnitDossiers, rows: list[dict]) -> list[str]:
    """Each inverse link whose sides end on two items after the swap: refused when their interop failed, else every
    swapped side declares unverified_interop unless it passed."""
    replaced = {r["scope"]: r for r in rows}
    ends = {d.key: d.current for d in unit.dossiers} | {s.scope: s.current for s in unit.stays}
    ends |= {k: r["option"] for k, r in replaced.items()}
    return [p for k in unit.unit.links if k.kind == INVERSE for p in _link(k, unit, ends, replaced)]


def _output_differs(unit: UnitDossiers, member: str, item: str | None) -> bool:
    d = next(d for d in unit.dossiers if d.key == member)
    return any(o.item == item and o.diff is not None and o.diff.output != SAME for o in d.options)


def _link(k: Link, unit: UnitDossiers, ends: dict[str, str | None], replaced: dict[str, dict]) -> list[str]:
    swapped = [m for m in (k.a, k.b) if m in replaced]
    if not swapped or ends[k.a] == ends[k.b]:
        return []
    alias, status = unit.aliases(), unit.interop(ends[k.a], ends[k.b])
    # another output format on one side only: the other side can no longer read it, whatever interop says
    if any(_output_differs(unit, m, ends[m]) for m in swapped):
        return [f"{alias[k.a]} and {alias[k.b]} are inverse; another output must end both on one item"]
    return _interop_of_ends(k, unit, ends, replaced, swapped, status)


def _interop_of_ends(k: Link, unit: UnitDossiers, ends: dict[str, str | None], replaced: dict[str, dict],
                     swapped: list[str], status: str) -> list[str]:
    alias = unit.aliases()
    if status == "fail":
        return [f"{alias[k.a]} and {alias[k.b]} are inverse, and {ends[k.a]} and {ends[k.b]} failed their interop check"]
    if status == "pass":
        return []
    other = {k.a: k.b, k.b: k.a}
    return [f"{alias[m]}: risks must include unverified_interop: its inverse {alias[other[m]]} ends on "
            f"{ends[other[m]] or 'an unresolved item'}, and their interop is {status}"
            for m in swapped if "unverified_interop" not in replaced[m]["risks"]]


def check_reply(text: str, unit: UnitDossiers, max_change: str = DROP_IN) -> tuple[dict | None, list[str]]:
    """max_change: the dossiers' own; an option above it is refused even when listed."""
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
        problems.append("keep names members; a keep covers every member with options and has none")
    if decision == "replace":
        rows = _members(members, unit, reason, problems, max_change)
    if problems:
        return None, problems
    if decision == "keep":
        rows = [Replacement(d.key, "keep", None, (), (), reason).to_json() for d in unit.dossiers]
    return {"replacements": rows}, []
