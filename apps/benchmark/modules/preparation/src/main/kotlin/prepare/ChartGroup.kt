package io.github.junekim0007.cryptobench.preparation.prepare

import io.github.junekim0007.cryptobench.preparation.key.plan.KeyRecipe

/** Which cases a chart may compare. Ids are stable; names follow docs/cryptography/primitives.md. Unidentified is always 0. */
enum class ChartGroup(val id: Int, val label: String) {
    UNIDENTIFIED(0, "unidentified"),
    SYMMETRIC_CIPHER(1, "symmetric-cipher"),
    ASYMMETRIC_CIPHER(2, "asymmetric-cipher"),
    SIGNATURE(3, "signature"),
    HASH(4, "hash"),
    MAC(5, "mac"),
    KEM(6, "kem"),
    KEY_AGREEMENT(7, "key-agreement"),
    KEYGEN_SYMMETRIC(8, "keygen-symmetric"),
    KEYGEN_ASYMMETRIC(9, "keygen-asymmetric");

    companion object {

        // The JCA service type decides; Cipher covers both kinds, so its key kind splits it.
        fun of(type: String, key: KeyRecipe): ChartGroup = when (type.uppercase()) {
            "CIPHER" -> when (key) {
                is KeyRecipe.Secret -> SYMMETRIC_CIPHER
                is KeyRecipe.Pair -> ASYMMETRIC_CIPHER
                else -> UNIDENTIFIED
            }
            "SIGNATURE" -> SIGNATURE
            "MESSAGEDIGEST" -> HASH
            "MAC" -> MAC
            "KEM" -> KEM
            "KEYAGREEMENT" -> KEY_AGREEMENT
            "KEYGENERATOR" -> KEYGEN_SYMMETRIC
            "KEYPAIRGENERATOR" -> KEYGEN_ASYMMETRIC
            else -> UNIDENTIFIED
        }
    }
}
