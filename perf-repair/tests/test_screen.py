import json
from dataclasses import replace
from pathlib import Path

import pytest

from perfrepair.catalog.names import Names
from perfrepair.catalog.screening import Screening
from perfrepair.check.run import validate_run
from perfrepair.data_handler.inbound.__main__ import main as inbound
from perfrepair.dto.grouping import Item, read_items
from helpers import with_results, CATALOG
from perfrepair.dto.screen import Verdict, lowers_status, read_screen, screen_document
from perfrepair.grouping.build.stage import build_stage
from perfrepair.screen.handler import ScreeningHandler
from perfrepair.validation.screen import validate_screen, validate_screen_document
from perfrepair.screen.catalog import screening_catalog
from perfrepair.validation.screen import _verdict_problems

F = Path(__file__).parent / "fixtures" / "results" / "test-api36-00000000" / "manifest.yaml"
NAMES = Names.load()
HANDLER = ScreeningHandler(Screening.load(names=NAMES), NAMES)


def status(engine_type, name, provider="P", target_sdk=None):
    return HANDLER.verdict(engine_type, name, provider, target_sdk).status


@pytest.mark.parametrize("engine_type, name, expected", [
    ("MessageDigest", "MD5", "broken"), ("MessageDigest", "SHA-256", "accepted"),
    ("MessageDigest", "sha256", "accepted"), ("MessageDigest", "SHA", "broken"),
    ("Signature", "SHA256WithRSA", "accepted"), ("Signature", "SHA1withRSA", "broken"),
    ("Mac", "HMAC-SHA1", "accepted"), ("Cipher", "AESWrap", "accepted"),
    ("Cipher", "PBEWITHSHAAND3-KEYTRIPLEDES-CBC", "broken")])
def test_a_crypto_row_answers_every_spelling_of_its_name(engine_type, name, expected):
    assert status(engine_type, name) == expected


@pytest.mark.parametrize("name, expected", [
    ("DES/CBC/PKCS5Padding", "broken"), ("TripleDES/CBC/NoPadding", "broken"), ("Blowfish/CTR/NoPadding", "broken"),
    ("AES/ECB/PKCS7Padding", "broken"), ("Rijndael/ECB/NoPadding", "broken"), ("AES_256/GCM/NoPadding", "accepted"),
    ("AES/CBC/PKCS5Padding", "accepted"), ("RSA/ECB/OAEPWithSHA-256AndMGF1Padding", "accepted"),
    ("RSA/NONE/OAEPPadding", "accepted"), ("RSA/ECB/PKCS1Padding", "broken")])
def test_component_rules_deprecate_a_base_or_a_chaining_mode(name, expected):
    assert status("Cipher", name) == expected


def test_a_verdict_records_the_canonical_key_it_was_screened_by():
    verdict = HANDLER.verdict("Cipher", "AES_256/ECB/NoPadding", "P")
    assert (verdict.status, verdict.canonical, verdict.keySize) == ("broken", "AES/ECB/NoPadding", 256)
    assert validate_screen({1: replace(verdict, canonical=None)}, ITEMS[:1]) == [
        "1: broken without the canonical name it was screened by"]


def test_a_component_verdict_cites_its_rule():
    verdict = HANDLER.verdict("Cipher", "ARCFOUR/ECB/NoPadding", "P")
    assert verdict.status == "broken" and "rfc7465" in verdict.source


def test_ecb_is_nominal_only_where_the_catalog_maps_a_mode_onto_it():
    assert status("Cipher", "RSA/ECB/OAEPWithSHA-1AndMGF1Padding") == "accepted"
    assert status("Cipher", "AES/ECB/NoPadding") == "broken"


@pytest.mark.parametrize("target_sdk, expected", [(None, "accepted"), (27, "accepted"), (28, "platform_deprecated"),
                                                  (36, "platform_deprecated")])
def test_the_platform_gate_compares_the_target_sdk(target_sdk, expected):
    assert status("MessageDigest", "SHA-256", "BC", target_sdk) == expected


def test_platform_rows_are_per_provider():
    assert status("MessageDigest", "SHA-256", "AndroidOpenSSL", 36) == "accepted"


def test_a_name_off_the_platform_list_stays_accepted_at_any_target_sdk():
    assert status("KeyPairGenerator", "RSA", "BC", 36) == "accepted"
    assert status("KeyPairGenerator", "EC", "BC", 36) == "platform_deprecated"


def test_broken_outranks_platform_deprecated():
    assert status("MessageDigest", "MD5", "BC", 36) == "broken"


def test_a_platform_row_without_a_crypto_row_is_unknown_until_gated():
    assert status("KeyFactory", "RSA", "BC") == "unknown"
    assert status("KeyFactory", "RSA", "BC", 28) == "platform_deprecated"


@pytest.mark.parametrize("engine_type, name, want, cited", [
    ("Cipher", "PBEWITHSHA256AND128BITAES-CBC-BC", "broken", "rfc7292"),
    ("Cipher", "PBEWITHSHA1AND256BITAES-CBC-BC", "broken", "rfc7292"),
    ("Cipher", "PBEWITHSHAANDTWOFISH-CBC", "broken", "rfc7292"),
    ("Cipher", "PBEWITHMD5AND192BITAES-CBC-OPENSSL", "broken", "rfc8018"),
    ("Cipher", "DESedeWrap/CBC/NoPadding", "broken", "800-131Ar2.pdf"),
    ("Signature", "NONEWITHDSA", "broken", "186-5.pdf"),
    ("Signature", "ML-DSA-65", "accepted", "FIPS.204.pdf"),
    ("KeyPairGenerator", "ML-KEM-768", "accepted", "FIPS.203.pdf")])
def test_a_scheme_is_judged_by_what_its_source_says(engine_type, name, want, cited):
    verdict = HANDLER.verdict(engine_type, name, "P")
    assert verdict.status == want and verdict.source.endswith(cited)


@pytest.mark.parametrize("engine_type, name", [
    ("Cipher", "PBEWithHmacSHA256AndAES_256"), ("MessageDigest", "SHAKE128-256"), ("KeyStore", "PKCS12"),
    ("Cipher", "AES/GCM-SIV/NoPadding"), ("Cipher", "AES_256/GCM-SIV/NoPadding"), ("Signature", "NONEwithRSA"),
    ("Signature", "NONEwithECDSA"), ("Signature", "HSS/LMS"), ("Mac", "PBEWithHmacSHA1"), ("Mac", "HmacPBESHA256")])
def test_an_unlisted_name_is_unknown_without_a_source(engine_type, name):
    verdict = HANDLER.verdict(engine_type, name, "P")
    assert (verdict.status, verdict.reason, verdict.source) == ("unknown", "no screening row", None)


def test_a_name_conflict_is_unknown_with_its_code():
    names = replace(NAMES, conflicts={("MessageDigest", "MD5"): "P says MD5, Q says MD4"})
    verdict = ScreeningHandler(HANDLER.screening, names).verdict("MessageDigest", "md5", "P")
    assert verdict.status == "unknown" and verdict.reason.startswith("name_conflict:")
    assert _verdict_problems(1, verdict, None) == []
    assert _verdict_problems(1, replace(verdict, reason="no screening row"), None) == ["1: unknown without the canonical name it was screened by"]


BUILT = {"items": "a" * 64, "profiles": "b" * 64}
ITEMS = [Item(1, "MessageDigest", "MD5", "P", "f"), Item(2, "MessageDigest", "SHA-256", "P", "f")]


def test_the_validator_wants_one_verdict_per_item_from_the_status_set():
    verdicts = {1: Verdict("weak", "r", "s"), 3: Verdict("broken", "r", None, "MD5")}
    assert validate_screen(verdicts, ITEMS) == ["2: no verdict", "3: verdict for no item",
                                                "1: status 'weak' is not one of ['broken', 'platform_deprecated', 'unverified', "
                                                "'accepted', 'unknown']", "3: broken without a source"]


def test_the_validator_refuses_another_schema_version():
    doc = screen_document({1: Verdict("broken", "r", "s", "MD5"), 2: Verdict("accepted", "r", "s", "SHA-256")}, CATALOG,
                          BUILT)
    assert validate_screen_document(doc, ITEMS, BUILT) == []
    assert validate_screen_document({**doc, "schemaVersion": 1}, ITEMS, BUILT)[0].startswith("screen.json does not parse")


def test_a_model_sourced_verdict_needs_the_review_screen_json_records():
    verdicts = {1: Verdict("broken", "withdrawn", "model:" + "f" * 12, "MD5"), 2: Verdict("accepted", "r", "s", "SHA-256")}
    unreviewed = screen_document(verdicts, CATALOG, BUILT)
    assert validate_screen_document(unreviewed, ITEMS, BUILT) == [
        "1: broken from model:ffffffffffff, but screen.json records no review"]
    other = screen_document(verdicts, CATALOG, BUILT, "e" * 12)
    assert validate_screen_document(other, ITEMS, BUILT) == [
        "1: broken from model:ffffffffffff, but screen.json was reviewed under eeeeeeeeeeee"]
    assert validate_screen_document(screen_document(verdicts, CATALOG, BUILT, "f" * 12), ITEMS, BUILT) == []


def test_the_validator_refuses_verdicts_built_from_other_items_or_profiles():
    doc = screen_document({1: Verdict("broken", "r", "s", "MD5"), 2: Verdict("accepted", "r", "s", "SHA-256")}, CATALOG,
                          BUILT)
    assert validate_screen_document(doc, ITEMS, {**BUILT, "items": "c" * 64}) == [
        "built from another items.json (sha256 aaaaaaaaaaaa), this run's is cccccccccccc; rerun grouping build"]
    assert validate_screen_document(doc, ITEMS, {**BUILT, "profiles": None})[0].startswith("built from another profiles")


@pytest.fixture
def built(tmp_path):
    assert inbound(["--device-results", str(with_results(tmp_path))]) == 0
    return build_stage(F, tmp_path, screening_catalog(None))


def test_build_writes_a_verdict_per_item_beside_items_json(built):
    items = read_items(json.loads(built.items.read_text()))
    verdicts = read_screen(json.loads(built.screen.read_text()))
    assert set(verdicts) == {i.id for i in items}
    assert {v.status for v in verdicts.values()} == {"accepted"}


def test_validate_run_checks_screen_json(built):
    run = built.root.parent
    assert validate_run(run, screening_catalog(None))["grouping/screen.json"] == []
    doc = json.loads(built.screen.read_text())
    doc["verdicts"].pop("1")
    built.screen.write_text(json.dumps(doc))
    assert validate_run(run, screening_catalog(None))["grouping/screen.json"] == ["1: no verdict"]


A, B = Verdict("accepted", "r", "S", "SHA-256"), Verdict("broken", "r", "S", "MD5")
PLATFORM = replace(A, status="platform_deprecated")


@pytest.mark.parametrize("current, target, lowers", [
    (A, A, False), (A, B, True), (B, B, False), (B, replace(B, keySize=128), False), (None, B, True), (B, None, False),
    (A, PLATFORM, True), (PLATFORM, PLATFORM, False), (PLATFORM, A, False)])
def test_a_screened_out_target_never_lowers_the_status(current, target, lowers):
    assert lowers_status(current, target) is lowers


def test_for_app_raises_a_recorded_verdict_only_at_the_gate():
    recorded = HANDLER.verdict("MessageDigest", "SHA-256", "BC")
    assert HANDLER.for_app(recorded, "MessageDigest", "BC", 27) == recorded
    assert HANDLER.for_app(recorded, "MessageDigest", "BC", 28) == HANDLER.verdict("MessageDigest", "SHA-256", "BC", 28)
    broken = HANDLER.verdict("MessageDigest", "MD5", "BC")
    assert HANDLER.for_app(broken, "MessageDigest", "BC", 36) == broken
