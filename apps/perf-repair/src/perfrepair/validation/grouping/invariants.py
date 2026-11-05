"""Grouping invariants over groups.json, profiles.json, checks.json, screen.json and the apps' dossiers: is each group right."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from ...dto.grouping import KEY_APP_HELD, KEY_PROVIDER_HELD
from ...dto.screen import CODE_GROUPED
from ..finding import ADVISORY, BLOCKING, Violation

UNKNOWN = "unknown"
DECIDING = ("known", "convention")
# checks.json kinds report computes and nothing blocks on: each one belongs to the invariant it names
STORED = {"key_contract_differs": "key_contract_agrees", "resolved_parameters_differ": "signature_agrees"}


@dataclass(frozen=True)
class Grouping:
    groups: dict
    profiles: dict[str, dict]
    checks: list[dict]
    canonical: dict[str, str | None]


def _multi(g: Grouping) -> list[dict]:
    return [x for x in g.groups["groups"] if len(x["members"]) > 1]


def _qualified(g: Grouping, m: int) -> str:
    return g.groups["items"][str(m)]["qualified"]


def _components(g: Grouping, m: int) -> dict[str, dict]:
    sig = (g.profiles.get(str(m)) or {}).get("signature") or {}
    return {c["name"]: c for c in sig.get("components") or []}


def _stored(g: Grouping, invariant: str, fix: str) -> list[Violation]:
    return [Violation(invariant, BLOCKING, f"group {f['group']}", (f"group {f['group']}", f"checks.json {f['kind']}: {f['detail']}"), fix)
            for f in g.checks if STORED.get(f.get("kind")) == invariant and f.get("group")]


def _never_offered(g: Grouping, dossiers: dict[str, dict]) -> set[str]:
    """Groups every member screened out and no dossier offers; a screened-out item stays an option of its own algorithm."""
    offered = {o.get("item") for doc in dossiers.values() for d in doc.get("dossiers") or [] for o in d.get("options") or []}
    return {x["id"] for x in g.groups["groups"]
            if all(g.groups["items"][str(m)].get("screen") in CODE_GROUPED for m in x["members"])
            and not any(_qualified(g, m) in offered for m in x["members"])}


def key_contract_agrees(g: Grouping, dossiers: dict[str, dict]) -> list[Violation]:
    """Both key contracts in one group, or a member whose key component nothing recorded: `unknown` decides nothing."""
    fix = "split the group by key contract; record each member's key contract before it is grouped"
    exempt = _never_offered(g, dossiers)
    out = [v for v in _stored(g, "key_contract_agrees", fix) if v.subject.removeprefix("group ") not in exempt]
    for x in (x for x in _multi(g) if x["id"] not in exempt):
        contracts = {m: g.groups["items"][str(m)].get("keyContract") for m in x["members"]}
        asked = [m for m in x["members"] if (_components(g, m).get("key") or {}).get("status") == UNKNOWN]
        mixed = {KEY_APP_HELD, KEY_PROVIDER_HELD} <= set(contracts.values())
        if asked and not mixed:
            out.append(Violation("key_contract_agrees", BLOCKING, f"group {x['id']}",
                                 (f"group {x['id']}", *(f"{_qualified(g, m)} keyContract {contracts[m]}, key component unknown"
                                                       for m in asked)), fix))
    return out


def signature_agrees(g: Grouping) -> list[Violation]:
    """Members that both know a component know one value; resolved parameters as report's own finding says."""
    fix = "split the group where the members' components differ, or correct the signature that misread one"
    out = _stored(g, "signature_agrees", fix)
    for x in _multi(g):
        values: dict[str, dict] = defaultdict(dict)
        for m in x["members"]:
            for name, c in _components(g, m).items():
                if name != "key" and c.get("status") in DECIDING and c.get("value") is not None:
                    values[name].setdefault(str(c["value"]), []).append(_qualified(g, m))
        for name, seen in sorted(values.items()):
            if len(seen) > 1:
                out.append(Violation("signature_agrees", BLOCKING, f"group {x['id']}",
                                     (f"group {x['id']}", *(f"{name}={v}: {', '.join(q)}" for v, q in sorted(seen.items()))), fix))
    return out


def no_runnable_no_options(g: Grouping, dossiers: dict[str, dict]) -> list[Violation]:
    """A group none of whose members runs here was never measured: no dossier offers one of its members."""
    dead = {_qualified(g, m): x["id"] for x in g.groups["groups"] if not x.get("runnable") for m in x["members"]}
    out = []
    for app, doc in sorted(dossiers.items()):
        for d in doc.get("dossiers") or []:
            for o in d.get("options") or []:
                if o.get("item") in dead:
                    out.append(Violation("no_runnable_no_options", BLOCKING, f"{app} scope {d['scope']['id']}",
                                         (f"{app}/dossiers.json scope {d['scope']['id']} option {o.get('alias')} {o['item']}",
                                          f"group {dead[o['item']]} has no runnable member"),
                                         "rerun the dossier step; an option must be a member that runs on this device"))
    return out


def interop_not_run(g: Grouping) -> list[Violation]:
    """Advisory: the options stay labelled not_run and a replace declares unverified_interop; nothing measured them."""
    if (g.groups.get("interop") or {}).get("status") != "not_run":
        return []
    return [Violation("interop_not_run", ADVISORY, f"group {x['id']}", (f"group {x['id']}", f"{len(x['runnable'])} runnable members"),
                      "run the guide with --device, or grouping interop-plan, cryptobenchmark --interop, interop-read")
            for x in g.groups["groups"] if len(x.get("runnable") or ()) > 1]


def _facts(g: Grouping, x: dict) -> set[tuple]:
    out = set()
    for m in x["members"]:
        entry = g.groups["items"][str(m)]
        comps = tuple(sorted((n, str(c.get("value"))) for n, c in _components(g, m).items()))
        out.add((entry.get("screen"), entry.get("keyContract"), comps))
    return out


def algorithm_split(g: Grouping) -> list[Violation]:
    """Advisory: one canonical name in several groups of a family with no recorded fact between them; a false split costs
    options, never a wrong join, and whether to merge is the model's call."""
    by_name: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for x in g.groups["groups"]:
        names = {g.canonical.get(str(m)) for m in x["members"]} - {None}
        for name in names:
            by_name[(x["family"], name)].append(x)
    out = []
    for (family, name), xs in sorted(by_name.items()):
        same = [x for x in xs if any(_facts(g, x) & _facts(g, y) for y in xs if y is not x)]
        if len(same) > 1:
            out.append(Violation("algorithm_split", ADVISORY, f"{family} {name}",
                                 tuple(f"group {x['id']}" for x in same) + ("members with equal recorded facts in each",),
                                 "merge the groups, or record the fact that splits them"))
    return out


def _partners(g: Grouping) -> dict[str, tuple[str, frozenset[str]]]:
    out = {}
    for x in g.groups["groups"]:
        names = frozenset(_qualified(g, m) for m in x["members"])
        for m in x["members"]:
            out[_qualified(g, m)] = (x["id"], names)
    return out


def _input(g: Grouping, qualified: str) -> str | None:
    ids = {e["qualified"]: k for k, e in g.groups["items"].items()}
    profile = dict(g.profiles.get(ids[qualified]) or {})
    return repr(sorted((k, profile.get(k)) for k in ("keyContract", "signature", "keyKind", "runs")))


def grouping_stable(g: Grouping, other: Grouping) -> list[Violation]:
    """Two items with the same recorded input in both runs are together in both or apart in both."""
    mine, theirs = _partners(g), _partners(other)
    same = sorted(q for q in set(mine) & set(theirs) if _input(g, q) == _input(other, q))
    out, seen = [], set()
    for a in same:
        for b in same:
            if a < b and (b in mine[a][1]) != (b in theirs[a][1]) and (a, b) not in seen:
                seen.add((a, b))
                here, there = ("together", "apart") if b in mine[a][1] else ("apart", "together")
                out.append(Violation("grouping_stable", BLOCKING, f"{a} and {b}",
                                     (f"group {mine[a][0]} / {mine[b][0]}: {here}", f"other run group {theirs[a][0]} / {theirs[b][0]}: {there}"),
                                     "the same input gave different groups; decide which run is right and rerun the other"))
    return out


def grouping_invariants(g: Grouping, dossiers: dict[str, dict], other: Grouping | None = None) -> list[Violation]:
    found = key_contract_agrees(g, dossiers) + signature_agrees(g) + no_runnable_no_options(g, dossiers) + interop_not_run(g)
    return found + algorithm_split(g) + (grouping_stable(g, other) if other is not None else [])
