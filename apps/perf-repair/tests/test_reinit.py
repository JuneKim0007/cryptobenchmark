"""reinit reads a role's lives per direction: a row's `use` says which direction needs it given, never which direction chooses it."""
import pytest

from perfrepair.catalog.algorithms import algorithms
from perfrepair.catalog.glossary import GlossaryError, direction_of, direction_problems, lives, role_problems, tree
from perfrepair.catalog.reinit import reinit
from perfrepair.catalog.views import view_for

PER_USE_ROLES = ("iv", "nonce")


def _use_decrypt() -> list:
    return [e for e in algorithms().entries if any(r["name"] in PER_USE_ROLES and r.get("use") == "decrypt" for r in e.raw["required"])]


def test_the_72_entries_a_decrypt_row_marks_choose_going_forward_and_copy_going_back():
    entries = _use_decrypt()
    assert len(entries) == 72
    for e in entries:
        assert {o: reinit(e.raw, o) for o in e.raw["operations"]["value"]} == {"encrypt": "perUse", "decrypt": "never"}, e.id


def test_the_reverse_value_is_copied_and_the_forward_value_new():
    for role in PER_USE_ROLES:
        assert (lives(role, "forward"), lives(role, "reverse")) == ("perUse", "copied")
    assert (lives("secretKey", "forward"), lives("secretKey", "reverse")) == ("once", "once")


@pytest.mark.parametrize("operation,direction", [("encrypt", "forward"), ("wrap", "forward"), ("sign", "forward"), ("computeMac", "forward"), ("agree", "forward"),
                                                 ("decrypt", "reverse"), ("unwrap", "reverse"), ("verify", "reverse")])
def test_every_operation_has_a_direction(operation, direction):
    assert direction_of(operation) == direction


def test_an_unknown_operation_is_coded():
    with pytest.raises(GlossaryError, match="no value 'colour'"):
        reinit({"required": [], "optional": []}, "colour")


@pytest.mark.parametrize("identifier,operation,expected", [
    ("Cipher|AES/CBC/PKCS5Padding", "encrypt", "perUse"), ("Cipher|AES/CBC/PKCS5Padding", "decrypt", "never"),
    ("Cipher|AES/ECB/PKCS5Padding", "encrypt", "never"), ("Mac|AES-GMAC", "computeMac", "perUse"), ("Mac|HmacSHA256", "computeMac", "never"),
    ("KeyAgreement|ECMQVWITHSHA256CKDF", "agree", "perUse"), ("KeyAgreement|ECDH", "agree", "never"), ("MessageDigest|SHA-256", "digest", "never"),
    ("Signature|SHA256withECDSA", "sign", "never"), ("Signature|SHA256withECDSA", "verify", "never")])
def test_other_engines_read_the_same_rule(identifier, operation, expected):
    assert reinit(view_for(identifier), operation) == expected


def test_an_optional_row_counts_and_the_build_s_own_rows_decide():
    assert not [r for r in view_for("Cipher|ChaCha20")["required"] if r["name"] in PER_USE_ROLES]
    assert reinit(view_for("Cipher|ChaCha20"), "encrypt") == "perUse"
    assert reinit(view_for("Cipher|AES/CBC/NoPadding", "BC @ jdk-25"), "encrypt") == "perUse"


def test_a_role_lives_in_closed_words_on_every_direction_and_operations_cover_the_list():
    assert role_problems() == [] and direction_problems() == []
    assert set(tree()["algorithm"]["operations"]["value"]["directions"]) == set(tree()["algorithm"]["operations"]["value"]["values"])
