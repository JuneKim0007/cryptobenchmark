from grouping_data import BENCHMARK, FAMILIES, INVENTORY, NAMES, PREPARED, PROBE, TRIAL

from perfrepair.dto.grouping import Item, items_document, profiles_document, read_items, read_profiles
from perfrepair.grouping.build.items import build
from perfrepair.validation.grouping.items import validate_items


def built():
    return build(PROBE, NAMES, TRIAL, FAMILIES, INVENTORY, PREPARED, BENCHMARK)


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


def test_probe_and_trial_suffice_and_what_they_cannot_say_is_null():
    items, profiles = build(PROBE, NAMES, TRIAL, FAMILIES)
    full_items, full = built()
    assert items == full_items
    item, p = by_name(items, profiles)[("ALG-S/M1", "P1")]
    assert (p.measured, p.preparedKeySizes, p.runs) == (None, None, full[item.id].runs)
    assert read_profiles(profiles_document(profiles)) == profiles
    assert profiles_document(profiles)["profiles"][str(item.id)]["measured"] is None


def test_a_probe_only_device_folder_builds_and_reports_no_key_sizes(tmp_path):
    import yaml
    from helpers import with_results
    from perfrepair.grouping.build.stage import build_stage
    from perfrepair.grouping.report.rules import common_key_sizes
    from perfrepair.screen.catalog import screening_catalog
    folder = with_results(tmp_path)
    doc = yaml.safe_load((folder / "manifest.yaml").read_text())
    doc["files"] = {k: doc["files"][k] for k in ("probe", "trial")}
    (folder / "manifest.yaml").write_text(yaml.safe_dump(doc))
    paths = build_stage(folder / "manifest.yaml", folder, screening_catalog(None))
    profiles = read_profiles(yaml.safe_load(paths.profiles.read_text()))
    assert all(p.measured is None and p.preparedKeySizes is None for p in profiles.values())
    assert common_key_sizes(list(profiles), profiles) == []


def test_build_with_a_missing_input_is_a_one_line_error(tmp_path, capsys):
    from perfrepair.grouping.__main__ import main
    manifest = tmp_path / "manifest.yaml"
    manifest.write_text("schemaVersion: 1\nfiles: {}\n")
    assert main(["build", "--device-results", str(tmp_path)]) == 1
    log, error = capsys.readouterr().err.splitlines()
    assert log == "device.screening.catalog: packaged catalog (no perfrepair.yaml); aiReview off"
    assert error.startswith("error ") and "Traceback" not in error
