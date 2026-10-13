from pathlib import Path

from perfrepair.repair.candidates import candidates
from perfrepair.repair.choose import choose
from perfrepair.repair.patch import rewrite
from perfrepair.repair.replay import compare, side
from perfrepair.repair.test_set import build_test_set
from perfrepair.validation.repair import validate_patch

GROUPS = {"items": {"1": {"qualified": "MessageDigest|SHA-256|P1", "group": "g"},
                    "2": {"qualified": "MessageDigest|SHA-256|P2", "group": "g"},
                    "3": {"qualified": "MessageDigest|X|P1", "group": "h"}},
          "groups": [{"id": "g", "runnable": [1, 2]}, {"id": "h", "runnable": [3]}]}


def site(literal_provider=None, expr="\"SHA-256\""):
    return {"file": "A.java", "line": 2, "snippet": "", "engineType": "MessageDigest",
            "algorithm": {"expr": expr, "literal": "SHA-256"},
            "provider": {"expr": f'"{literal_provider}"', "literal": literal_provider} if literal_provider else None,
            "resolvedProvider": "P1", "resolvedAlgorithm": "SHA-256", "resolution": "default"}


def test_a_site_joins_its_item_and_the_group_alternatives():
    [c] = candidates({"sites": [site(), {**site(), "resolution": "not_registered"}]}, GROUPS)
    assert (c.item, c.group, c.alternatives) == ("1", "g", ("2",))
    assert build_test_set([c], GROUPS, "app")["include"] == [{"provider": "P1", "type": "MessageDigest", "name": "SHA-256"},
                                                       {"provider": "P2", "type": "MessageDigest", "name": "SHA-256"}]


def test_only_a_test_verdict_with_a_pair_from_the_site_item_replaces_it():
    [c] = candidates({"sites": [site()]}, GROUPS)
    test = {"verdicts": [{"groupId": "g", "decision": "test", "reason": "r", "pairs": [{"from": "1", "to": "2", "reason": "faster"}]}]}
    skip = {"verdicts": [{"groupId": "g", "decision": "skip", "reason": "no", "pairs": []}]}
    assert choose([c], test)[0]["replacement"] == "2"
    assert choose([c], skip)[0]["replacement"] is None


def test_a_patch_pins_the_new_provider_and_changes_only_literals(tmp_path):
    (tmp_path / "A.java").write_text('class A {\n  MessageDigest md = MessageDigest.getInstance("SHA-256");\n}\n')
    [c] = candidates({"sites": [site()]}, GROUPS)
    patch = rewrite(c, "P1", "SHA-256", "P2", tmp_path)
    assert patch.after == 'MessageDigest.getInstance("SHA-256", "P2")'
    assert validate_patch(patch.to_json(), tmp_path) == []
    assert "+  MessageDigest md = MessageDigest.getInstance(\"SHA-256\", \"P2\");" in patch.diff(tmp_path)


def test_a_patch_that_rewrites_code_is_refused(tmp_path):
    (tmp_path / "A.java").write_text('x\nMessageDigest.getInstance("SHA-256")\n')
    bad = {"file": "A.java", "line": 2, "before": 'MessageDigest.getInstance("SHA-256")', "after": 'MessageDigest.getInstance(name)'}
    assert validate_patch(bad, tmp_path)


def test_replay_reports_speedup_and_energy():
    cases = [{"id": i, "type": "MessageDigest", "algorithm": "SHA-256", "provider": p, "inputSize": 64,
              "metrics": {"timeNs": {"runs": [t, t]}}} for i, p, t in (("a", "P1", 200.0), ("b", "P2", 100.0))]
    energy = {"cases": {"a": {"valid": True, "joulesPerOperation": 2e-6}, "b": {"valid": True, "joulesPerOperation": 1e-6}}}
    result = compare(side({"cases": cases}, energy, "MessageDigest", "SHA-256", "P1", 64),
                     side({"cases": cases}, energy, "MessageDigest", "SHA-256", "P2", 64))
    assert result["speedup"] == 2.0 and result["energyRatio"] == 0.5 and result["after"]["mbPerSecond"] == 640.0
