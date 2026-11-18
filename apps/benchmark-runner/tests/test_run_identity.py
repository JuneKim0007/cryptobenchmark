import yaml

from cryptobench.shared import paths
from cryptobench.shared.results import identity

PROBE = {"schemaVersion": 1, "runtime": {"model": "m", "fingerprint": "f", "sdkInt": 36}}
BUILD = {"securityPatch": "2026-10-05", "apex": {"com.android.conscrypt": 1, "com.android.art": 2}}


def discovery(tmp_path, facts=None):
    capture = tmp_path / "probe_20261117T000000Z.yaml"
    capture.write_text(yaml.safe_dump(PROBE))
    if facts is not None:
        paths.Discovery(tmp_path).facts.write_text(yaml.safe_dump(facts))
    return capture


def test_a_device_identity_is_the_runtime_with_the_build_facts_and_a_host_one_the_runtime_alone(tmp_path):
    assert identity.device(discovery(tmp_path)) == PROBE["runtime"]
    assert identity.device(discovery(tmp_path, {"schemaVersion": 1, "build": BUILD})) == {**PROBE["runtime"], "build": BUILD}


def test_suppressed_errors_are_a_set_whatever_their_order_and_spacing(tmp_path, monkeypatch):
    monkeypatch.setattr(identity, "code", lambda: "c")
    effective = tmp_path / "effective.yaml"
    effective.write_text(yaml.safe_dump({"run": {"seed": 0}}))
    of = lambda suppress: identity.of(effective, discovery(tmp_path), {"scheme": "interleaved"}, suppress)["suppressErrors"]
    assert of("UNLOCKED,EMULATOR") == of(" EMULATOR, UNLOCKED,") == ["EMULATOR", "UNLOCKED"] and of("") == []


def test_a_nested_change_is_named_by_its_dotted_path():
    before = {"schema": 2, "device": {"model": "m", "build": BUILD}, "order": {"scheme": "interleaved"}, "suppressErrors": []}
    after = {**before, "device": {"model": "m", "build": {**BUILD, "apex": {**BUILD["apex"], "com.android.art": 3}}},
             "order": {"scheme": "shuffled", "seed": 7}, "suppressErrors": ["UNLOCKED"]}
    assert identity.changed(before, after) == ["device.build.apex.com.android.art", "order", "suppressErrors"]
    assert identity.changed(before, {**before, "device": {"model": "m"}}) == ["device.build"]


def test_which_include_picked_an_entry_is_not_part_of_the_selection(tmp_path, monkeypatch):
    monkeypatch.setattr(identity, "code", lambda: "c")
    effective = tmp_path / "effective.yaml"

    def selection(entry):
        effective.write_text(yaml.safe_dump({"run": {}, "providers": {"SUN": {"MessageDigest": {"SHA-256": entry}}}}))
        return identity.of(effective, discovery(tmp_path), {}, "")["selection"]

    picked = lambda index: {"keySizes": [1], "from": {"testSet": "tier1.yaml", "includes": [{"index": index, "name": "SHA-256"}]}}
    assert selection(picked(0)) == selection(picked(3)) == selection({"keySizes": [1]}) != selection({"keySizes": [2]})
