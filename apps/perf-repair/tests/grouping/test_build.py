from grouping_data import BENCHMARK, FAMILIES, INVENTORY, NAMES, PREPARED, PROBE, TRIAL

from perfrepair.device.selection import exclusions
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
    assert all(i.type != "TypeX" for i in items)


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


def _with_transformations(*transformations):
    service = {"provider": "P1", "type": "TypeC", "algorithm": "ALG-T", "instantiates": True, "defaultRun": {"works": True},
               "transformations": list(transformations)}
    return {**TRIAL, "services": [*TRIAL["services"], service]}


def test_a_declared_transformation_that_ran_is_an_item_like_the_case_the_benchmark_measures():
    # a host provider declaring modes and paddings: the inventory holds these names, no service does
    ran = {"name": "ALG-T/M1/PAD", "instantiates": True, "defaultRun": {"works": True, "keyAlgorithm": "ALG-S"}}
    refused = {"name": "ALG-T/M1/BAD", "instantiates": False}
    items, profiles = build(PROBE, NAMES, _with_transformations(ran, refused), FAMILIES)
    names = {i.name: i for i in items}
    assert {"ALG-T", "ALG-T/M1/PAD"} <= set(names) and "ALG-T/M1/BAD" not in names
    assert profiles[names["ALG-T/M1/PAD"].id].instantiates and profiles[names["ALG-T/M1/PAD"].id].runs
    assert validate_items(items, profiles, FAMILIES) == []


def test_a_used_set_excludes_every_transformation_it_does_not_keep():
    ran = {"name": "ALG-T/M1/PAD", "instantiates": True, "defaultRun": {"works": True}}
    items, _ = build(PROBE, NAMES, _with_transformations(ran), FAMILIES)
    keep = frozenset({next(i for i in items if i.name == "ALG-T").qualified})
    assert {"provider": "P1", "type": "TypeC", "name": "ALG-T/M1/PAD"} in exclusions(items, None, keep)


def test_documents_round_trip_and_validate():
    items, profiles = built()
    assert read_items(items_document(items)) == items
    assert read_profiles(profiles_document(profiles)) == profiles
    assert validate_items(items, profiles, FAMILIES) == []


def test_validator_names_every_broken_contract():
    items, profiles = built()
    broken = [Item(1, "TypeC", "A", "P", "nope"), Item(3, "TypeD", "B", "P", "cipher.secret")]
    problems = validate_items(broken, {1: profiles[1]}, FAMILIES)
    assert any("not 1..2" in p for p in problems)
    assert any("'nope' is not in the catalog" in p for p in problems)
    assert any("is for TypeC, not TypeD" in p for p in problems)
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


def test_a_catalogued_name_a_provider_aliases_otherwise_keeps_the_catalog_name():
    from perfrepair.catalog.families import Families
    from perfrepair.catalog.names import Names
    from perfrepair.data_handler.inbound.probe import Probe
    probe = Probe({"providers": [
        {"name": "P1", "services": [{"type": "Mac", "algorithm": "HmacSHA256", "aliases": ["PBEWITHHMACSHA256"]}]},
        {"name": "P2", "services": [{"type": "Mac", "algorithm": "PBEWITHHMACSHA256"}]}]})
    names = probe.names(Names.load())
    trial = {"services": [{"provider": "P2", "type": "Mac", "algorithm": "PBEWITHHMACSHA256", "instantiates": True},
                          {"provider": "P1", "type": "Mac", "algorithm": "HmacSHA256", "instantiates": True}]}
    assert ("Mac", "PBEWITHHMACSHA256") in names.conflicts
    assert names.canonical("Mac", "PBEWITHHMACSHA256").name == "PBEWithHmacSHA256"
    items, _ = build(probe, names, trial, Families.load())
    assert [i.name for i in items] == ["HmacSHA256", "PBEWITHHMACSHA256"]


def test_a_generator_service_whose_name_is_a_conflict_is_built_not_stopped():
    from perfrepair.catalog.families import Families
    from perfrepair.catalog.names import Names
    from perfrepair.data_handler.inbound.probe import Probe
    probe = Probe({"providers": [
        {"name": "P1", "services": [{"type": "KeyGenerator", "algorithm": "HmacSHA256", "aliases": ["FAKEKEY"]},
                                    {"type": "Mac", "algorithm": "HmacSHA256"}]},
        {"name": "P2", "services": [{"type": "KeyGenerator", "algorithm": "HmacSHA512", "aliases": ["FAKEKEY"]}]},
        {"name": "P3", "services": [{"type": "KeyGenerator", "algorithm": "FAKEKEY"}]}]})
    names = probe.names(Names.load())
    assert ("KeyGenerator", "FAKEKEY") in names.conflicts
    trial = {"services": [{"provider": "P3", "type": "KeyGenerator", "algorithm": "FAKEKEY", "instantiates": True},
                          {"provider": "P1", "type": "Mac", "algorithm": "HmacSHA256", "instantiates": True,
                           "keyAlgorithm": "FAKEKEY"}]}
    items, profiles = build(probe, names, trial, Families.load())
    assert sorted(i.name for i in items) == ["FAKEKEY", "HmacSHA256"]
    assert not next(profiles[i.id] for i in items if i.name == "FAKEKEY").signature.decided


def test_build_with_a_missing_input_is_a_one_line_error(tmp_path, capsys):
    from perfrepair.grouping.__main__ import main
    manifest = tmp_path / "manifest.yaml"
    manifest.write_text("schemaVersion: 1\nfiles: {}\n")
    assert main(["build", "--device-results", str(tmp_path)]) == 1
    log, error = capsys.readouterr().err.splitlines()
    assert log == "device.screening.catalog: packaged catalog (no perfrepair.yaml); aiReview off"
    assert error.startswith("error ") and "Traceback" not in error
