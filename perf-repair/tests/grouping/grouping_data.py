from perfrepair.dto.grouping import Family
from perfrepair.grouping.catalog.families import Families

FAMILIES = Families([
    Family("cipher.secret", "TypeC", "secret", "secret ciphers"),
    Family("cipher.pair", "TypeC", "pair", "pair ciphers"),
    Family("cipher.unknown", "TypeC", "unknown", "unknown ciphers"),
    Family("digest.none", "TypeD", "none", "digests"),
])


def service(type_, name, aliases=(), attributes=None):
    s = {"type": type_, "algorithm": name}
    if aliases:
        s["aliases"] = list(aliases)
    if attributes:
        s["attributes"] = attributes
    return s


PROBE = {"providers": [
    {"name": "P1", "precedence": 1, "services": [
        service("TypeC", "ALG-S/M1"), service("TypeC", "ALG-P/X"), service("TypeD", "H1"),
        service("TypeC", "ALG-RAW", attributes={"SupportedKeyFormats": ["RAW"]}),
        service("KeyGenerator", "KS", aliases=["ks-alias"]), service("KeyPairGenerator", "KP")]},
    {"name": "P2", "precedence": 2, "services": [service("TypeC", "ALG-S/M1"), service("TypeC", "PASSWORD-ALG"),
                                                 service("TypeX", "OUT-OF-SCOPE")]},
]}
TRIAL = {"services": [
    {"provider": "P1", "type": "TypeC", "algorithm": "ALG-S/M1", "instantiates": True,
     "defaultRun": {"works": True, "keyAlgorithm": "KS", "keyProvider": "P1", "keySize": 128, "providerChose": "M1 iv=16B"}},
    {"provider": "P2", "type": "TypeC", "algorithm": "ALG-S/M1", "instantiates": True,
     "defaultRun": {"works": True, "keyAlgorithm": "ks-alias", "keyProvider": "P1", "keySize": 128}},
    {"provider": "P1", "type": "TypeC", "algorithm": "ALG-P/X", "instantiates": True,
     "defaultRun": {"works": True, "keyAlgorithm": "KP", "keySize": 2048}},
    {"provider": "P1", "type": "TypeC", "algorithm": "ALG-RAW", "instantiates": True,
     "defaultRun": {"works": False, "error": "SomeException: no key"}},
    {"provider": "P2", "type": "TypeC", "algorithm": "PASSWORD-ALG", "instantiates": True,
     "defaultRun": {"works": False, "error": "NoSuchAlgorithmException: no provider generates PASSWORD-ALG"}},
    {"provider": "P1", "type": "TypeD", "algorithm": "H1", "instantiates": True, "defaultRun": {"works": True}},
    {"provider": "P2", "type": "TypeX", "algorithm": "OUT-OF-SCOPE", "instantiates": True},
]}
INVENTORY = {"providers": {"P2": {"TypeC": {"PASSWORD-ALG": {"runs": False, "reason": "no provider generates PASSWORD-ALG"}}}}}
PREPARED = {"cases": [
    {"id": "c1", "provider": "P1", "type": "TypeC", "algorithm": "ALG-S/M1", "keySize": 128, "key": {"kind": "secret"}},
    {"id": "c2", "provider": "P1", "type": "TypeC", "algorithm": "ALG-S/M1", "keySize": 256, "key": {"kind": "secret"}},
]}
BENCHMARK = {"cases": [{"id": "c1", "provider": "P1", "type": "TypeC", "algorithm": "ALG-S/M1"}]}
