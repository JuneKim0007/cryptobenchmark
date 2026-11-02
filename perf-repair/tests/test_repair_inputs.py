from pathlib import Path

import pytest

from perfrepair.files import write_text
from perfrepair.repair.inputs import configured, read_effective, scope_inputs
from repair_fixture import JAVA, scope

RESULTS = Path(__file__).parent / "fixtures" / "results"
A, B = "Cipher|AES/GCM/NoPadding|P", "Cipher|AES/GCM/NoPadding|Q"
EFFECTIVE = {"run": {"inputSizes": [64, 1024, 16384]}, "providers": {
    "P": {"Cipher": {"AES/GCM/NoPadding": {"keySizes": [128, 256]},
                     "AES/GCM/NoPadding@short": {"keySizes": [192], "inputSizes": [32]}}},
    "Q": {"Cipher": {"AES/GCM/NoPadding": {"inputSizes": [64, 1024], "keySizes": [256]},
                     "ChaCha20": {"providerDefaults": ["keySize"]}}}}}
SEAL = scope(JAVA, "byte[] literal(byte[] in)", 'Cipher.getInstance("AES/GCM/NoPadding", "Slow")')


def test_an_item_unions_its_groups_and_takes_the_run_sizes_when_it_sets_none():
    assert configured(EFFECTIVE, A) == ({32, 64, 1024, 16384}, {128, 192, 256})
    assert configured(EFFECTIVE, B) == ({64, 1024}, {256})
    assert configured(EFFECTIVE, "Cipher|aes/gcm/NOPADDING|Q") == configured(EFFECTIVE, B)
    assert configured(EFFECTIVE, "Cipher|ChaCha20|Q") == ({64, 1024, 16384}, set())


def test_run_inputs_are_the_largest_sizes_both_items_were_configured_at():
    assert scope_inputs(SEAL, A, B, EFFECTIVE) == {"inputSize": 1024, "keySize": 256, "from": "run"}


def test_no_common_size_stays_null_and_is_never_guessed():
    effective = {**EFFECTIVE, "providers": {**EFFECTIVE["providers"],
                                            "Q": {"Cipher": {"AES/GCM/NoPadding": {"inputSizes": [48]}}}}}
    assert scope_inputs(SEAL, A, B, effective) == {"inputSize": None, "keySize": None, "from": "run"}


def test_the_apps_static_size_wins_over_the_run():
    app = scope(JAVA, "byte[] literal(byte[] in)", 'Cipher.getInstance("AES/GCM/NoPadding", "Slow")', inputSize=48)
    assert scope_inputs(app, A, B, EFFECTIVE) == {"inputSize": 48, "keySize": None, "from": "app"}


def test_an_item_the_run_did_not_configure_is_a_coded_error():
    with pytest.raises(ValueError, match="item_not_configured: Cipher|AES/GCM/NoPadding|R"):
        scope_inputs(SEAL, A, "Cipher|AES/GCM/NoPadding|R", EFFECTIVE)


def test_effective_yaml_is_found_through_the_manifest(tmp_path):
    assert read_effective(RESULTS / "manifest.yaml")["run"]["inputSizes"] == [64, 1024]
    write_text(tmp_path / "manifest.yaml", "schemaVersion: 1\nmode: device\nfiles: {}\n")
    with pytest.raises(ValueError, match="missing_effective"):
        read_effective(tmp_path / "manifest.yaml")
