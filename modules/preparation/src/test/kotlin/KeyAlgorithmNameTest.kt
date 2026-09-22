package io.github.junekim0007.cryptobench.preparation.key.plan

import org.junit.Assert.assertEquals
import org.junit.Test

class KeyAlgorithmNameTest {

    @Test
    fun derivesTheKeyAlgorithmFromTheOperationName() {
        listOf(
            Triple("Cipher", "AES/GCM/NoPadding", "AES"),
            Triple("Cipher", "RSA/ECB/OAEPWithSHA-256AndMGF1Padding", "RSA"),
            Triple("Cipher", "ChaCha20", "ChaCha20"),
            Triple("Signature", "SHA256withRSA", "RSA"),
            Triple("Signature", "SHA256WithECDSA", "EC"),
            Triple("Signature", "Ed25519", "Ed25519"),
            Triple("Signature", "RSASSA-PSS", "RSASSA-PSS"),
            Triple("KeyAgreement", "ECDH", "EC"),
            Triple("KeyAgreement", "X25519", "X25519"),
            Triple("Mac", "HmacSHA256", "HmacSHA256"),
        ).forEach { (type, algorithm, key) ->
            assertEquals("$type/$algorithm", key, KeyAlgorithmName.candidates(type, algorithm).first().algorithm)
        }
    }

    /** Tried in order until the device has a generator: what environment's default run also falls back to. */
    @Test
    fun cipherCandidatesFallBackToTheFamily() {
        assertEquals(listOf(KeyCandidate("ChaCha20-Poly1305"), KeyCandidate("ChaCha20")), KeyAlgorithmName.candidates("Cipher", "ChaCha20-Poly1305"))
        assertEquals(listOf(KeyCandidate("AES_128"), KeyCandidate("AES", 128)), KeyAlgorithmName.candidates("Cipher", "AES_128/GCM/NoPadding"))
        assertEquals(listOf(KeyCandidate("EC")), KeyAlgorithmName.candidates("Signature", "SHA256withECDSA"))
    }
}
