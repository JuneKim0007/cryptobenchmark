from dataclasses import replace

import pytest

from perfrepair.catalog.types import Types
from perfrepair.dto.change import CHANGES, REJECT_REASONS, admits
from perfrepair.dto.lifecycle import BOUNDED, Lifecycle, Requirement, Settled
from perfrepair.dto.site import Scope, scope_id
from perfrepair.dto.types import Properties, Strength, TypeRow
from perfrepair.result.change import Candidate, classify, reach

TYPES = Types({}, {"blockKey": {128: 128, 256: 256}}, frozenset({"digest", "ciphertext"}), {"S": "x"})


def row(name, kind="digest", *, auth=False, det=True, nonce="none", params="none", out=32, key="none",
        strength=Strength(bits=128), min_sdk=1) -> TypeRow:
    return TypeRow("fam", name, kind, Properties(auth, det, nonce, params, out, key), strength, "S", min_sdk, "S")


def scope(sinks=("return",), params_origin=None, key_source="unknown", key_size=None) -> Scope:
    reqs = (Requirement("parameters", params_origin, 3, 4),) if params_origin else ()
    return Scope(scope_id("app", "A.java", "f", 3, "TypeA.getInstance"), "app", "A.java", 3, "TypeA.getInstance", "f", 1, 9,
                 "TypeA", "ALG-A", "P1", "default", key_size, None, tuple(sinks), key_source,
                 Lifecycle(BOUNDED, (), "local", (), reqs))


def cand(r, measured=True, bundled=False, lowers=False) -> Candidate:
    return Candidate(f"TypeA|{r.canonical}|P1", r, measured, bundled, lowers)


WEAK, STRONG = row("HASH-A", out=16, strength=Strength(bits=0)), row("HASH-B", out=32, strength=Strength(bits=128))


def test_a_longer_stronger_digest_returned_is_a_local_edit():
    c = classify(TYPES, scope(), WEAK, cand(STRONG), 21)
    assert (c.change, c.diff.output, c.diff.input, c.diff.key, c.diff.reach) == ("local-edit", "bytes", "same", "same", "return")


@pytest.mark.parametrize("sinks", [("persist",), ("network",), ("unknown",), ("local", "persist")])
def test_an_output_that_leaves_the_function_is_a_migration(sinks):
    c = classify(TYPES, scope(sinks), WEAK, cand(STRONG), 21)
    assert (c.change, c.diff.reach) == ("migration", "persist")


def test_reach_local_return_persist():
    assert [reach(scope(s)) for s in (("local",), ("local", "return"), ("network",))] == ["local", "return", "persist"]


def test_a_key_type_change_is_a_migration():
    a, b = row("MAC-A", "tag", auth=True, key="K1"), row("MAC-B", "tag", auth=True, key="K2")
    c = classify(TYPES, scope(("local",)), a, cand(b), 21)
    assert (c.change, c.diff.key) == ("migration", "type")


def test_a_key_size_change_is_local_only_for_a_key_made_in_the_function():
    a = row("C-A", "ciphertext", det=False, nonce="unpredictable", params="iv", key="K", strength=Strength(key="blockKey"))
    b = replace(a, canonical="C-B", strength=Strength(bits=256))
    assert classify(TYPES, scope(("local",), key_size=128), a, cand(b), 21).change == "migration"
    generated = classify(TYPES, scope(("local",), key_source="generated", key_size=128), a, cand(b), 21)
    assert (generated.change, generated.diff.key) == ("local-edit", "size")


def test_a_different_output_kind_is_a_migration():
    a = row("C-A", "ciphertext", det=False, nonce="unique", params="iv", key="K")
    b = replace(a, canonical="C-B", outputKind="aead_ciphertext", properties=replace(a.properties, authenticated=True))
    c = classify(TYPES, scope(("local",), params_origin="generated"), a, cand(b), 21)
    assert (c.change, c.diff.output) == ("migration", "kind")


@pytest.mark.parametrize("origin,want", [("generated", "reshaped"), ("literal", "reshaped"), ("derived", "reshaped"),
                                         ("parameter", "new_parameter"), (None, "new_parameter")])
def test_a_changed_parameter_shape_is_reshaped_only_when_built_in_the_function(origin, want):
    a = row("C-A", "ciphertext", det=False, nonce="unique", params="iv", key="K")
    b = replace(a, canonical="C-B", properties=replace(a.properties, parameters="other"))
    c = classify(TYPES, scope(("local",), params_origin=origin), a, cand(b), 21)
    assert c.diff.input == want and c.change == ("local-edit" if want == "reshaped" else "migration")


def test_a_parameter_the_current_call_never_passes_is_new():
    a = row("C-A", "ciphertext", det=False, key="K")
    b = replace(a, canonical="C-B", properties=replace(a.properties, parameters="iv"))
    assert classify(TYPES, scope(("local",)), a, cand(b), 21).diff.input == "new_parameter"


def test_a_settled_origin_counts_for_the_parameter():
    s = scope(("local",))
    req = Requirement("parameters", "field", 3, 4, (), Settled("generated", 2))
    s = replace(s, lifecycle=replace(s.lifecycle, requirements=(req,)))
    a = row("C-A", "ciphertext", det=False, nonce="unpredictable", params="iv", key="K")
    b = replace(a, canonical="C-B", properties=replace(a.properties, nonceRequired="unique"))
    assert classify(TYPES, s, a, cand(b), 21).change == "local-edit"


def _rejected(current, candidate, s=None, min_sdk=21):
    c = classify(TYPES, s or scope(), current, candidate, min_sdk)
    assert c.change == "rejected"
    return set(c.reasons)


def test_reject_strength_below():
    assert _rejected(STRONG, cand(WEAK)) == {"strength_below"}


def test_reject_strength_unknown():
    assert _rejected(WEAK, cand(replace(STRONG, strength=Strength()))) == {"strength_unknown"}


def test_reject_strength_unknown_without_the_key_size():
    a = row("C-A", "ciphertext", det=False, key="K", strength=Strength(key="blockKey"))
    assert _rejected(a, cand(replace(a, canonical="C-B", strength=Strength(bits=256))), scope(("local",))) == {"strength_unknown"}


def test_reject_authenticated_lost():
    a = row("C-A", "aead_ciphertext", auth=True, det=False, nonce="unique", params="gcm", key="K")
    b = row("C-B", "ciphertext", det=False, nonce="unique", params="gcm", key="K")
    assert _rejected(a, cand(b), scope(("local",), params_origin="generated")) == {"authenticated_lost"}


def test_reject_deterministic_lost_where_relied_on():
    a = row("C-A", "ciphertext", key="K")
    assert _rejected(a, cand(replace(a, canonical="C-B", properties=replace(a.properties, deterministic=False)))) \
        == {"deterministic_lost"}


def test_deterministic_lost_on_an_output_not_compared_is_allowed():
    a = row("S-A", "signature", auth=True, key="K")
    b = replace(a, canonical="S-B", properties=replace(a.properties, deterministic=False))
    assert classify(TYPES, scope(), a, cand(b), 21).change == "local-edit"


@pytest.mark.parametrize("origin", ["literal", "parameter", None])
def test_reject_a_stricter_nonce_unless_the_iv_is_generated(origin):
    a = row("C-A", "ciphertext", det=False, nonce="unpredictable", params="iv", key="K")
    b = replace(a, canonical="C-B", properties=replace(a.properties, nonceRequired="unique"))
    assert "nonce_not_generated" in _rejected(a, cand(b), scope(("local",), params_origin=origin))


def test_reject_unavailable_at_the_app_min_sdk_unless_bundled():
    late = replace(STRONG, minSdk=28)
    assert _rejected(WEAK, cand(late), min_sdk=21) == {"unavailable"}
    assert classify(TYPES, scope(), WEAK, cand(late, bundled=True), 21).change == "local-edit"


@pytest.mark.parametrize("candidate_sdk,app_sdk", [(None, 21), (2, None)])
def test_reject_availability_unknown(candidate_sdk, app_sdk):
    assert _rejected(WEAK, cand(replace(STRONG, minSdk=candidate_sdk)), min_sdk=app_sdk) == {"availability_unknown"}


def test_a_name_in_every_release_needs_no_app_min_sdk():
    assert classify(TYPES, scope(), WEAK, cand(replace(STRONG, minSdk=1)), None).change == "local-edit"


def test_reject_not_measured_deprecated_and_type_unknown():
    assert _rejected(WEAK, cand(STRONG, measured=False)) == {"not_measured"}
    assert _rejected(WEAK, cand(STRONG, lowers=True)) == {"deprecated"}
    assert _rejected(None, cand(STRONG)) == {"type_unknown"}
    assert _rejected(WEAK, Candidate("TypeA|X|P1", None, True, False, False)) == {"type_unknown"}


def test_every_reason_is_listed_and_reasons_accumulate():
    found = _rejected(STRONG, cand(replace(WEAK, minSdk=None), measured=False, lowers=True))
    assert found == {"strength_below", "availability_unknown", "not_measured", "deprecated"} <= set(REJECT_REASONS)


def test_max_change_admits_its_class_and_those_before_it():
    assert [admits("local-edit", c) for c in CHANGES] == [True, True, False]
    assert not admits("migration", "rejected")
