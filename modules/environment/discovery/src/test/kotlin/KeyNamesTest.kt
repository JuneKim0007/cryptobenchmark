package io.github.junekim0007.cryptobench.discovery.trial.call

import org.junit.Assert.assertEquals
import org.junit.Test

class KeyNamesTest {

    /** A size written into a registered name is a contract of that name, not a choice. */
    @Test
    fun cipherCandidatesKeepASizeWrittenIntoTheName() {
        assertEquals(listOf("AES" to null), KeyNames.cipherCandidates("AES/GCM/NoPadding"))
        assertEquals(listOf("AES_128" to null, "AES" to 128), KeyNames.cipherCandidates("AES_128/GCM/NoPadding"))
        assertEquals(listOf("ChaCha20-Poly1305" to null, "ChaCha20" to null), KeyNames.cipherCandidates("ChaCha20-Poly1305"))
    }

    @Test
    fun signatureAndAgreementKeys() {
        assertEquals("RSA", KeyNames.signatureKey("SHA256withRSA"))
        assertEquals("EC", KeyNames.signatureKey("SHA256WithECDSA"))
        assertEquals("DSA", KeyNames.signatureKey("SHA256withDSAinP1363Format"))
        assertEquals("Ed25519", KeyNames.signatureKey("Ed25519"))
        assertEquals("EC", KeyNames.agreementKey("ECDH"))
        assertEquals("X25519", KeyNames.agreementKey("X25519"))
    }
}
