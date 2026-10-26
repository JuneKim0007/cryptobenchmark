package io.github.junekim0007.cryptobench.preparation.measurement

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

        private val ASYMMETRIC_CIPHERS = listOf("RSA", "ECIES", "ELGAMAL")

        /** The JCA service type decides; the name only splits Cipher, which covers both kinds. SHA or RSA inside another type's name never counts. */
        fun of(type: String, algorithm: String): ChartGroup = when (type.uppercase()) {
            "CIPHER" -> if (ASYMMETRIC_CIPHERS.any { algorithm.uppercase().startsWith(it) }) ASYMMETRIC_CIPHER else SYMMETRIC_CIPHER
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
