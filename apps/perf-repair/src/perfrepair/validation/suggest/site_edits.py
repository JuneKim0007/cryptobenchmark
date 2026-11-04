"""A reply's edits against the chosen option: each kind once, the field it fills, the kinds the option requires."""
from __future__ import annotations

from ...dto.dossier import Option, pin_text
from ...dto.grouping import algorithm_of, provider_of
from ...dto.replacement import EDIT_FIELDS, EDIT_KIND_TABLE, EDIT_KINDS, Edit


def text_field(d: dict, field: str) -> str | None:
    return d.get(field) if isinstance(d.get(field), str) else None


def _parameters(raw, where: str, problems: list[str]) -> dict[str, str]:
    if not isinstance(raw, list):
        problems.append(f"{where}: parameters is not a list")
        return {}
    out = {}
    for j, p in enumerate(raw):
        if not isinstance(p, dict) or text_field(p, "name") is None or text_field(p, "value") is None:
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
    values = {"provider": text_field(e, "provider"), "algorithm": text_field(e, "algorithm"),
              "parameters": _parameters(e.get("parameters"), where, problems)}
    problems += [f"{where}: {kind} takes no {f}" for f in EDIT_FIELDS if f != field and values[f]]
    want = takes(kind, option.item, option.pins)
    problems += _CHECK[field](kind, values[field], want, option, where)
    return Edit(kind, **{field: want})


def required_kinds(option: Option, current: str) -> list[str]:
    """The kinds whose value for the option differs from the current call's."""
    return [k for k in EDIT_KINDS if takes(k, option.item, option.pins) != takes(k, current, {})]


def check_edits(raw: list, option: Option | None, current: str, problems: list[str]) -> list[Edit]:
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
        problems += [f"{where}: {f} is not a string" for f in ("provider", "algorithm") if text_field(e, f) is None]
        if option is not None:
            edits.append(_resolve(kind, e, option, where, problems))
    if option is not None:
        for kind in required_kinds(option, current):
            if kind not in kinds:
                want, have = takes(kind, option.item, option.pins), takes(kind, current, {})
                problems.append(_MISSING[EDIT_KIND_TABLE[kind].field](kind, want, have, option))
    return edits
