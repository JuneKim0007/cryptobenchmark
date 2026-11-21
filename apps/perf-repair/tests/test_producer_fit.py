"""A producer feeds a consumer's key parameter when their catalogue entries' key types are one; an unknown side cannot rule the pair out."""
from dataclasses import replace

from perfrepair.dto.site import Scope, scope_id
from perfrepair.scope.units.producers import _family_fits

BASE = Scope(scope_id("app", "A.java", "f", 3, "T.getInstance"), "app", "A.java", 3, "T.getInstance", "f", 1, 9, "KeyGenerator", "AES", None, "default")


def fits(producer, consumer):
    return _family_fits(replace(BASE, engineType=producer[0], algorithm=producer[1]), replace(BASE, engineType=consumer[0], algorithm=consumer[1]))


def test_the_key_types_decide():
    assert fits(("KeyGenerator", "AES"), ("Cipher", "AES/GCM/NoPadding"))
    assert fits(("KeyGenerator", "ChaCha20"), ("Cipher", "ChaCha20-Poly1305"))
    assert fits(("KeyPairGenerator", "EC"), ("Signature", "SHA256withECDSA"))
    assert not fits(("KeyGenerator", "CHACHA"), ("Cipher", "ChaCha20-Poly1305"))
    assert not fits(("KeyGenerator", "AES"), ("Mac", "HmacSHA256"))


def test_an_unknown_side_cannot_rule_the_pair_out():
    assert fits(("KeyGenerator", "NoSuchGenerator"), ("Cipher", "AES/GCM/NoPadding"))
    assert fits(("KeyGenerator", None), ("Cipher", "AES/GCM/NoPadding"))
