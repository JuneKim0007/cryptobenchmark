"""An algorithm's type: the family and output kind of what its call returns, its properties, strength and availability."""
from __future__ import annotations

from dataclasses import asdict, dataclass

OUTPUT_KINDS = ("digest", "tag", "ciphertext", "aead_ciphertext", "signature", "shared_secret", "secret_key", "key_pair")
# none: no IV or nonce; unpredictable: a fresh random IV each call; unique: never repeated under one key
NONCES = ("none", "unpredictable", "unique")
NO_NONCE = "none"
NO_PARAMETERS = "none"


@dataclass(frozen=True)
class Properties:
    """parameters: the shape of the parameter object the call passes (none, iv, gcm, ...); outputBytes None: varies."""
    authenticated: bool
    deterministic: bool
    nonceRequired: str
    parameters: str
    outputBytes: int | None
    keyType: str


@dataclass(frozen=True)
class Strength:
    """bits: a fixed strength; key: a keyStrength map the key size reads, capped by cap; neither: unknown."""
    bits: int | None = None
    key: str | None = None
    cap: int | None = None

    @property
    def known(self) -> bool:
        return self.bits is not None or self.key is not None


@dataclass(frozen=True)
class TypeRow:
    """minSdk None: the platform reference names no open-ended level; availability is checked on the device."""
    family: str
    canonical: str
    outputKind: str
    properties: Properties
    strength: Strength
    strengthSource: str
    minSdk: int | None
    minSdkSource: str

    def to_json(self) -> dict:
        return asdict(self)
