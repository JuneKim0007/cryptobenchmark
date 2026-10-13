from grouping_data import BENCHMARK, FAMILIES, INVENTORY, PREPARED, PROBE, TRIAL

from perfrepair.dto.grouping import Item, items_document, profiles_document, read_items, read_profiles
from perfrepair.grouping.build.items import build
from perfrepair.validation.grouping.items import validate_items


def built():
    return build(PROBE, TRIAL, INVENTORY, PREPARED, BENCHMARK, FAMILIES)


def by_name(items, profiles):
    return {(i.name, i.provider): (i, profiles[i.id]) for i in items}


def test_universe_is_the_catalogued_engine_types_with_ids_in_family_order():
    items, _ = built()
    assert [i.id for i in items] == [1, 2, 3, 4, 5, 6]
    assert [i.family for i in items] == ["cipher.pair", "cipher.secret", "cipher.secret", "cipher.secret",
                                         "cipher.unknown", "digest.none"]
    assert all(i.type != "TypeX" and i.group is None for i in items)


def test_each_key_kind_rule_decides_where_it_should():
    got = {k: (p.keyKind, p.keyKindFrom) for k, (_, p) in by_name(*built()).items()}
    assert got[("ALG-S/M1", "P1")] == ("secret", "measured")
    assert got[("ALG-S/M1", "P2")] == ("secret", "key_generator")
    assert got[("ALG-P/X", "P1")] == ("pair", "key_generator")
    assert got[("ALG-RAW", "P1")] == ("secret", "declared")
    assert got[("PASSWORD-ALG", "P2")] == ("unknown", "none")
    assert got[("H1", "P1")] == ("none", "engine_type")


def test_profile_carries_runs_reasons_and_what_was_prepared_and_measured():
    rows = by_name(*built())
    item, p = rows[("ALG-S/M1", "P1")]
    assert item.resolved == "M1 iv=16B" and p.measured and p.preparedKeySizes == (128, 256)
    _, password = rows[("PASSWORD-ALG", "P2")]
    assert not password.runs and "no provider generates" in password.reason


def test_documents_round_trip_and_validate():
    items, profiles = built()
    assert read_items(items_document(items)) == items
    assert read_profiles(profiles_document(profiles)) == profiles
    assert validate_items(items, profiles, FAMILIES) == []


def test_validator_names_every_broken_contract():
    items, profiles = built()
    broken = [Item(1, "TypeC", "A", "P", "nope"), Item(3, "TypeD", "B", "P", "cipher.secret", group="g")]
    problems = validate_items(broken, {1: profiles[1]}, FAMILIES)
    assert any("not 1..2" in p for p in problems)
    assert any("'nope' is not in the catalog" in p for p in problems)
    assert any("is for TypeC, not TypeD" in p for p in problems)
    assert any("carries group" in p for p in problems)
    assert any("3: no profile" in p for p in problems)
