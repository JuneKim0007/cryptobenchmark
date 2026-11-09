"""One algorithm keeps one identity across results, compacted rows, device items and catalogs."""
from pathlib import Path

import pytest
import yaml
from perfrepair import run_dir as rd
from cryptobench.catalogue.groups import group_catalog
from perfrepair.catalog.identity import UNSAFE, case_id_pattern, resolve
from cryptobench.catalogue.names import Names
from perfrepair.files import write_json
from perfrepair.run_dir import GroupingPaths
from perfrepair.validation.boundary import boundary_violations
from perfrepair.validation.finding import ADVISORY, BLOCKING

NAMES = Names.load()
ROOT = Path(__file__).parents[3]
CASE_ID = "Cipher_AES-CBC-PKCS5Padding_ENCRYPT_AndroidOpenSSL_k128_i64_WARM_p16e64aab_fixed"
ROW = {"rowId": CASE_ID, "type": "Cipher", "algorithm": "AES/CBC/PKCS5Padding", "provider": "AndroidOpenSSL", "operation": "ENCRYPT",
       "keySize": 128, "inputSize": 64, "phase": "WARM", "variant": "fixed"}
ITEM = {"id": 1, "type": "Cipher", "name": "AES/CBC/PKCS5Padding", "provider": "AndroidOpenSSL", "family": "cipher.secret"}
VERDICT = {"status": "accepted", "canonical": "AES/CBC/PKCS5Padding"}


@pytest.fixture
def device(tmp_path):
    paths = GroupingPaths(tmp_path)
    paths.root.mkdir()
    write_json(tmp_path / rd.ROWS, {"rows": [ROW]})
    write_json(tmp_path / rd.MEASUREMENTS, {"measurements": {CASE_ID: {}}})
    write_json(paths.items, {"items": [ITEM]})
    write_json(paths.screen, {"verdicts": {"1": VERDICT}})
    write_json(tmp_path / rd.USED, {"items": [{"item": "Cipher|AES/CBC/PKCS5Padding|AndroidOpenSSL"}]})
    return tmp_path


def invariants(found, severity):
    return {v.invariant for v in found if v.severity == severity}


def test_a_consistent_run_has_no_finding(device):
    assert boundary_violations(device, NAMES) == []


def test_a_folder_with_nothing_yet_has_no_finding(tmp_path):
    assert boundary_violations(tmp_path, NAMES) == []


@pytest.mark.parametrize("change", [{"keySize": 256}, {"provider": "BC"}, {"algorithm": "AES/GCM/NoPadding"}, {"variant": "notFixed"}])
def test_an_id_that_differs_from_its_row_is_blocking(device, change):
    write_json(device / rd.ROWS, {"rows": [{**ROW, **change}]})
    assert "case_id_reads_back" in invariants(boundary_violations(device, NAMES), BLOCKING)


def test_rows_and_measurements_holding_other_ids_are_blocking(device):
    write_json(device / rd.MEASUREMENTS, {"measurements": {"other": {}}})
    assert "ids_agree" in invariants(boundary_violations(device, NAMES), BLOCKING)


def test_two_rows_in_one_table_cell_are_blocking(device):
    other = {**ROW, "rowId": CASE_ID.replace("p16e64aab", "p00000000")}
    write_json(device / rd.ROWS, {"rows": [ROW, other]})
    write_json(device / rd.MEASUREMENTS, {"measurements": {CASE_ID: {}, other["rowId"]: {}}})
    assert "primitives_cell_is_one_row" in invariants(boundary_violations(device, NAMES), BLOCKING)


def test_a_measured_case_with_no_item_is_blocking(device):
    write_json(GroupingPaths(device).items, {"items": [{**ITEM, "provider": "BC"}]})
    assert {"measured_case_is_an_item", "used_is_an_item"} <= invariants(boundary_violations(device, NAMES), BLOCKING)


def test_a_registered_name_holding_the_separator_is_blocking(device):
    write_json(GroupingPaths(device).items, {"items": [ITEM, {**ITEM, "id": 2, "name": "my cipher|v2"}]})
    assert "item_id_parses" in invariants(boundary_violations(device, NAMES), BLOCKING)


def test_catalog_gaps_are_advisory_and_a_used_item_with_no_measurement_is_reported(device):
    write_json(GroupingPaths(device).items, {"items": [ITEM, {**ITEM, "id": 2, "name": "FUTURE-KEM", "type": "KeyPairGenerator", "family": "keypairgen.none"},
                                                       {**ITEM, "id": 3, "name": "AES/GCM/NoPadding"}]})
    write_json(GroupingPaths(device).screen, {"verdicts": {"1": VERDICT, "2": {"canonical": "FUTURE-KEM"}, "3": {"canonical": "AES/GCM/NoPadding"}}})
    write_json(device / rd.USED, {"items": [{"item": "Cipher|AES/CBC/PKCS5Padding|AndroidOpenSSL"}, {"item": "Cipher|AES/GCM/NoPadding|AndroidOpenSSL"}]})
    found = boundary_violations(device, NAMES)
    assert {"names_agree", "name_is_in_its_group", "used_is_measured"} <= invariants(found, ADVISORY)
    assert not invariants(found, BLOCKING)


def test_resolve_keeps_what_was_registered_and_joins_the_catalog():
    known = resolve("Cipher", "AES/CBC/PKCS5PADDING", "BC", "cipher.secret", NAMES)
    assert known.item == "Cipher|AES/CBC/PKCS5PADDING|BC"
    assert known.algorithm == "Cipher|AES/CBC/PKCS5Padding" and known.row == group_catalog().of("cipher.secret", "AES/CBC/PKCS5Padding").id
    unknown = resolve("Cipher", "my-cipher", "P", "unidentified", NAMES)
    assert (unknown.canonical, unknown.row, unknown.algorithm) == (None, None, "Cipher|my-cipher")


def test_a_name_listed_under_two_engine_types_has_two_algorithm_ids():
    mac, generator = (resolve(t, "HmacSHA1", "P", f, NAMES) for t, f in (("Mac", "mac.secret"), ("KeyGenerator", "keygen.none")))
    assert mac.algorithm != generator.algorithm


def test_a_case_id_written_by_the_harness_reads_back():
    assert case_id_pattern(ROW).match(CASE_ID)
    no_key = {"type": "MessageDigest", "algorithm": "SHA-512/256", "operation": "DIGEST", "provider": "BC", "inputSize": 64, "phase": "WARM", "variant": "fixed"}
    assert case_id_pattern(no_key).match("MessageDigest_SHA-512-256_DIGEST_BC_i64_WARM_fixed")


def test_no_two_catalog_names_share_a_case_id_part():
    for engine_type, spellings in NAMES.names.items():
        seen = {}
        for canonical in set(spellings.values()):
            assert seen.setdefault(UNSAFE.sub("-", canonical).lower(), canonical) == canonical, engine_type

