"""Screening, code-made groups and the don't-lower-the-status rule over every recorded runtime in fixtures/runtimes."""
from collections import Counter
from dataclasses import replace
from functools import cache
from pathlib import Path

import pytest

from helpers import ANY_EVIDENCE
from perfrepair.catalog.families import Families
from perfrepair.catalog.names import Names, fold
from perfrepair.catalog.screening import Screening
from perfrepair.data_handler.inbound.probe import Probe
from perfrepair.dto.interop import interop_section
from perfrepair.dto.grouping import KEY_PROVIDER_HELD
from helpers import ANY_EVIDENCE
from perfrepair.dto.screen import BROKEN, CODE_GROUPED, NEVER_TARGET, PLATFORM_DEPRECATED, RANK, STATUSES, lowers_status
from perfrepair.dto.site import Scope, scope_id
from perfrepair.files import read_document
from perfrepair.grouping.build.items import build
from perfrepair.result.dossier import build_dossiers
from perfrepair.screen.groups import code_group_id, code_groups
from perfrepair.screen.handler import ScreeningHandler
from perfrepair.validation.dossiers import validate_dossiers
from perfrepair.validation.screen import validate_screen

ROOT = Path(__file__).parent / "fixtures" / "runtimes"
RUNTIMES = sorted(p.name for p in ROOT.iterdir() if p.is_dir())
TARGET_SDKS = (None, 24, 27, 28, 33, 36)
CATALOG, FAMILIES = Names.load(), Families.load()
SCREENING = Screening.load(names=CATALOG)
PACKAGED = ScreeningHandler(SCREENING, CATALOG)

# a catalog change that moves these is deliberate: recompute, review, then pin
EXPECTED = {
    "android36": {"items": 168, "broken": 49, "accepted": 99, "unknown": 20, "codeGroups": 44, "multiProvider": 1,
                  "pairs": 25116, "refused": 10686},
    "jdk17": {"items": 193, "broken": 38, "accepted": 123, "unknown": 32, "codeGroups": 36, "multiProvider": 0,
              "pairs": 39084, "refused": 12264},
    "jdk21": {"items": 200, "broken": 38, "accepted": 123, "unknown": 39, "codeGroups": 36, "multiProvider": 0,
              "pairs": 41316, "refused": 14088},
    "jdk25": {"items": 214, "broken": 38, "accepted": 123, "unknown": 53, "codeGroups": 36, "multiProvider": 0,
              "pairs": 45984, "refused": 17004},
}


def load(runtime):
    probe = Probe(read_document(ROOT / runtime / "probe.yaml"))
    names = probe.names(CATALOG)
    items, profiles = build(probe, names, read_document(ROOT / runtime / "trial.yaml"), FAMILIES)
    handler = ScreeningHandler(SCREENING, names)
    return items, {i.id: replace(handler.verdict(i.type, i.name, i.provider),
                                 providerHeld=profiles[i.id].keyContract == KEY_PROVIDER_HELD) for i in items}


@cache
def loaded(runtime):
    return load(runtime)


def test_every_runtime_fixture_has_pinned_expectations():
    assert RUNTIMES == sorted(EXPECTED)


@pytest.mark.parametrize("runtime", RUNTIMES)
def test_each_item_gets_one_verdict_and_the_counts_are_pinned(runtime):
    items, verdicts = loaded(runtime)
    assert validate_screen(verdicts, items) == []
    counts = Counter(v.status for v in verdicts.values())
    want = EXPECTED[runtime]
    assert len(items) == want["items"]
    assert {s: counts[s] for s in STATUSES} == {s: want.get(s, 0) for s in STATUSES}


@pytest.mark.parametrize("runtime", RUNTIMES)
def test_every_screened_out_item_is_in_exactly_the_code_group_its_key_implies(runtime):
    items, verdicts = loaded(runtime)
    groups = code_groups(items, verdicts, {})
    by_id = {i.id: i for i in items}
    placed = Counter(m for g in groups.values() for m in g.members)
    out = {i.id for i in items if verdicts[i.id].status in CODE_GROUPED}
    assert set(placed) == out and set(placed.values()) == {1}
    for gid, g in groups.items():
        keys = {(by_id[m].family, verdicts[m].status, verdicts[m].canonical, verdicts[m].providerHeld) for m in g.members}
        assert len(keys) == 1 and all(code_group_id(by_id[m], verdicts[m]) == gid for m in g.members)
    multi = [g for g in groups.values() if len({by_id[m].provider for m in g.members}) > 1]
    assert (len(groups), len(multi)) == (EXPECTED[runtime]["codeGroups"], EXPECTED[runtime]["multiProvider"])
    assert multi or not runtime.startswith("android")

def _family_groups(items):
    """Worst case for the rule: one group per family holding every item of it."""
    return {"groups": [{"id": f"all.{f}", "members": sorted(i.id for i in items if i.family == f)}
                       for f in sorted({i.family for i in items})],
            "items": {str(i.id): {"qualified": i.qualified, "group": f"all.{i.family}", "runs": True} for i in items},
            "interop": interop_section(None)}


def _scope(item):
    call = item.qualified
    return Scope(scope_id("app", "A.java", "f", 1, call), "app", "A.java", 1, call, "f", 1, 1, item.type, item.name,
                 item.provider, "explicit")


@pytest.mark.parametrize("runtime", RUNTIMES)
def test_no_dossier_option_lowers_the_status_over_the_real_provider_mix(runtime, tmp_path):
    items, screen = loaded(runtime)
    (tmp_path / "A.java").write_text("void f() {}\n")
    groups, scopes = _family_groups(items), [_scope(i) for i in items]
    sizes, pairs, refused = Counter(i.family for i in items), 0, 0
    for sdk in TARGET_SDKS:
        verdicts = PACKAGED.app_verdicts(groups, screen, sdk)
        doc = build_dossiers("app", scopes, {"bundled": []}, groups, [], {}, tmp_path, verdicts, ANY_EVIDENCE)
        assert validate_dossiers(doc, scopes, groups, verdicts) == []
        offered = {d["current"]: {o["item"]: o["screen"] for o in d["options"]} for d in doc["dossiers"]}
        alone = {s.id for s, i in zip(scopes, items) if sizes[i.family] == 1}
        assert all(n["reason"] == ("no_alternative" if n["scope"] in alone else "deprecated_only")
                   for n in doc["noOptions"])
        for i in items:
            current = verdicts[i.qualified]
            others = [o for o in items if o.family == i.family and o.id != i.id]
            for o in others:
                target, shown = verdicts[o.qualified], offered.get(i.qualified, {}).get(o.qualified)
                pairs += 1
                refused += lowers_status(current, target)
                if target.status not in NEVER_TARGET:
                    assert shown == target.status
                    continue
                own = target.canonical == current.canonical
                allowed = own and RANK[target.status] >= RANK[current.status]
                assert (shown is not None) == allowed, (sdk, i.qualified, o.qualified)
                assert target.status != BROKEN or shown is None or own
    assert (pairs, refused) == (EXPECTED[runtime]["pairs"], EXPECTED[runtime]["refused"])


def _platform_rules(provider):
    return {(t, n): r for (p, t, n), r in SCREENING.platform.items() if p == provider}


def test_the_device_serves_none_of_the_names_removed_before_its_api():
    items, verdicts = loaded("android36")
    sdk = read_document(ROOT / "android36" / "probe.yaml")["runtime"]["sdkInt"]
    removed = {(p, t, n) for (p, t, n), r in SCREENING.platform.items() if r.removedApi and r.removedApi <= sdk}
    assert removed and not [i.qualified for i in items
                            if (i.provider, i.type, fold(verdicts[i.id].canonical or "")) in removed]
    for target_sdk in TARGET_SDKS:
        assert not [i for i in items if PACKAGED.for_app(verdicts[i.id], i.type, i.provider, target_sdk).status
                    == PLATFORM_DEPRECATED]


def test_the_platform_gate_flips_at_target_sdk_28_not_27():
    items, verdicts = loaded("android36")
    rules = _platform_rules("BC")
    # the device dropped BC's copies, so the gate is checked on the same names as AndroidOpenSSL serves them
    served = [(i, verdicts[i.id]) for i in items if i.provider == "AndroidOpenSSL"
              and verdicts[i.id].status != BROKEN and (i.type, fold(verdicts[i.id].canonical or "")) in rules]
    assert served
    for i, v in served:
        assert PACKAGED.for_app(v, i.type, "BC", 27) == v
        assert PACKAGED.for_app(v, i.type, "BC", 28).status == PLATFORM_DEPRECATED
        assert PACKAGED.for_app(v, i.type, i.provider, 36) == v


@pytest.mark.parametrize("runtime", RUNTIMES)
def test_code_group_ids_are_the_same_across_two_builds(runtime):
    first, again = loaded(runtime), load(runtime)
    assert first == again
    assert code_groups(*first, {}) == code_groups(*again, {})


def test_code_group_ids_are_the_same_across_runtimes_for_the_same_key():
    ids: dict[tuple, set[str]] = {}
    for runtime in RUNTIMES:
        items, verdicts = loaded(runtime)
        for i in items:
            v = verdicts[i.id]
            if v.status in CODE_GROUPED:
                ids.setdefault((i.family, v.status, v.canonical, v.providerHeld), set()).add(code_group_id(i, v))
    assert all(len(found) == 1 for found in ids.values())
    assert len({next(iter(found)) for found in ids.values()}) == len(ids)
    shared = [k for k in ids if all(any((i.family, verdicts[i.id].status, verdicts[i.id].canonical, verdicts[i.id].providerHeld) == k for i in items)
                                    for items, verdicts in map(loaded, RUNTIMES))]
    assert shared


@pytest.mark.parametrize("runtime", RUNTIMES)
def test_no_code_group_mixes_a_key_held_inside_the_provider_with_any_other(runtime):
    items, verdicts = loaded(runtime)
    for group in code_groups(items, verdicts, {}).values():
        assert len({verdicts[m].providerHeld for m in group.members}) == 1
