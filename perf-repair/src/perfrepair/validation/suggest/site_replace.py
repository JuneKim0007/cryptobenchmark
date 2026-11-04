"""Gate C of the replacement decision: a reply against its unit, in the aliases the model saw: every member with options
given an option of its own, or all of them kept; a member that stays is never named; an inverse pair left on two items
needs their interop."""
from __future__ import annotations

from ...dto.change import DROP_IN, admits
from ...dto.perf_mode import GENERIC_MODE, PerfMode
from ...dto.replacement import DECISIONS, OUTPUT_LEAVES, RECOMMEND, RISKS, Edit, Replacement, required_risks
from ...dto.dossier import Dossier, Option
from ...dto.site import Scope
from ...dto.unit import UnitDossiers
from ..json_reply import parse_object
from .site_edits import check_edits, text_field
from .site_inverse import inverse_problems
from .site_performance import concerns_of, metric_fields, performance, recommendable


def _risks(risks: list, scope: Scope, option: Option | None, decision: str) -> list[str]:
    problems = [f"risk {r!r} is not one of {RISKS}" for r in risks if r not in RISKS]
    problems += [f"risk {r!r} given more than once" for r in sorted({r for r in risks if isinstance(r, str)
                                                                       and risks.count(r) > 1})]
    if decision in ("replace", RECOMMEND):
        problems += [f"risks must include {r}: {' and '.join(words)}"
                     for r, words in required_risks(scope, option).items() if r not in risks]
    return problems


def output_leaves(risks: list, option: Option | None) -> list[str]:
    """A replace whose option changes the output, while its own risks say the output leaves the function."""
    leaving = [r for r in OUTPUT_LEAVES if r in risks]
    if option is None or not option.outputChanges or not leaving:
        return []
    problem = (f"{option.alias} changes the output and your risks {', '.join(leaving)} say the output leaves the function: "
               "decide recommend and list in needs what must follow, or choose an option with the same output; "
               "removing the risk does not change where the output goes")
    return [problem]


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


def _recommend_member(raw: dict, alias: str, dossier: Dossier, found: list[str]) -> Option | None:
    """Any change class can be recommended: nothing is applied."""
    by_alias = {o.alias: o for o in dossier.options}
    chosen = text_field(raw, "option")
    option = by_alias.get(chosen)
    if option is None:
        found.append(f"option {chosen!r} is not one of {', '.join(by_alias) or '(none)'}")
    found += ["a recommend applies no edit; edits is []"] if raw.get("edits") else []
    found += [p.removeprefix(f"{alias}: ") for p in recommendable(alias, option, raw.get("needs"))]
    return option


def _applied(raw: dict, dossier: Dossier, edits: list, max_change: str, found: list[str]) -> tuple[Option | None, list[Edit]]:
    option = _chosen(text_field(raw, "option"), {o.alias: o for o in dossier.options}, max_change, found)
    if not edits:
        found.append("replace names no edit")
    return option, check_edits(edits, option, dossier.current, found)


def _lists(raw: dict, found: list[str]) -> tuple[list, list]:
    edits, risks = raw.get("edits"), raw.get("risks")
    found += ["edits is not a list"] * (not isinstance(edits, list)) + ["risks is not a list"] * (not isinstance(risks, list))
    return edits if isinstance(edits, list) else [], risks if isinstance(risks, list) else []


def _replace_member(raw: dict, alias: str, dossier: Dossier, reason: str, problems: list[str],
                    max_change: str = DROP_IN, decision: str = "replace", picked: list | None = None) -> dict | None:
    """One member's option, edits and risks against its own dossier; its problems name the member."""
    found: list[str] = []
    edits, risks = _lists(raw, found)
    if decision == RECOMMEND:
        option, resolved = _recommend_member(raw, alias, dossier, found), []
    else:
        option, resolved = _applied(raw, dossier, edits, max_change, found)
        found += output_leaves(risks, option)
    found += _risks(risks, dossier.scope, option, decision)
    problems += [f"{alias}: {p}" for p in found]
    if found:
        return None
    if picked is not None:
        picked.append((alias, option))
    needs = tuple(n.strip() for n in raw.get("needs") or ()) if decision == RECOMMEND else ()
    return Replacement(dossier.key, decision, option.item, tuple(resolved), tuple(risks), reason, needs=needs).to_json()


def _staying(given: list, unit: UnitDossiers) -> list[str]:
    stayed = unit.stayed()
    return [f"member {a} has no option; it stays on {stayed[a].current or 'what it uses'}" for a in given if a in stayed]


def _members_named(given: list, unit: UnitDossiers) -> list[str]:
    aliased, problems = unit.aliased(), _staying(given, unit)
    problems += [f"member {a!r} is not one of {', '.join(aliased)}" for a in given if a not in aliased and a not in unit.stayed()]
    problems += [f"member {a} given more than once" for a in aliased if given.count(a) > 1]
    return problems + [f"replace covers every member with options: {a} is missing" for a in aliased if a not in given]


def _members(raw: list, unit: UnitDossiers, reason: str, problems: list[str], max_change: str, decision: str = "replace",
             picked: list | None = None) -> list[dict]:
    aliased = unit.aliased()
    given = [m.get("member") if isinstance(m, dict) else None for m in raw]
    problems += _members_named(given, unit)
    rows = []
    for alias, m in zip(given, raw):
        if alias in aliased and given.count(alias) == 1:
            rows.append(_replace_member(m, alias, aliased[alias], reason, problems, max_change, decision, picked))
    # a recommend is never applied, so the sides of its links stay where they are
    problems += [] if problems or decision == RECOMMEND else inverse_problems(unit, rows)
    return rows


def _with_fields(rows: list[dict], deciding: list[str], accepted: list[str], concerns: list[str]) -> list[dict]:
    return [{**r, "deciding": deciding, "accepted": accepted, "concerns": concerns} for r in rows]


def check_reply(text: str, unit: UnitDossiers, max_change: str = DROP_IN,
                perf: PerfMode = GENERIC_MODE) -> tuple[dict | None, list[str]]:
    """max_change: the dossiers' own; an option above it is refused even when listed. perf: the dossiers' perfMode,
    whose rule a replace's picks must meet."""
    d, problems = parse_object(text)
    if d is None:
        return None, problems
    decision, members, reason = d.get("decision"), d.get("members"), (text_field(d, "reason") or "").strip()
    problems = [p for p in (
        f"decision {decision!r} is not one of {DECISIONS}" if decision not in DECISIONS else "",
        "members is not a list" if not isinstance(members, list) else "",
        "reason is empty" if not reason else "",
    ) if p]
    members = members if isinstance(members, list) else []
    deciding, accepted, named = metric_fields(d)
    concerns, long = concerns_of(d)
    problems += named + long
    rows, picked = [], []
    if decision == "keep" and members:
        problems.append("keep names members; a keep covers every member with options and has none")
    if decision in ("replace", RECOMMEND):
        rows = _members(members, unit, reason, problems, max_change, decision, picked)
    if decision == "replace" and not problems:
        problems += performance(perf, picked, deciding, accepted)
    if problems:
        return None, problems
    if decision == "keep":
        rows = [Replacement(d.key, "keep", None, (), (), reason).to_json() for d in unit.dossiers]
    return {"replacements": _with_fields(rows, deciding, accepted, concerns)}, []
