package io.github.junekim0007.cryptobench.preparation

import io.github.junekim0007.cryptobench.preparation.peer.KeyUse
import io.github.junekim0007.cryptobench.preparation.port.Availability
import io.github.junekim0007.cryptobench.preparation.port.DeviceCapability
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

/** A generated key's use from a small catalogue: catalogue order, key type folded, Available on both providers, the type's timed operation from the entry's words. */
class KeyUseTest {

    private val cipher = """
        schemaVersion: 1
        family: cipher.secret
        algorithms:
          Cipher|AESWrap:
            key: {type: AES, origin: app, source: measured}
            operations: {value: [wrap, unwrap], source: measured}
          Cipher|AES/OnlyP:
            key: {type: AES, origin: app, source: measured}
            operations: {value: [encrypt, decrypt], source: measured}
          Cipher|AES:
            key: {type: aes, origin: app, source: measured}
            operations: {value: [encrypt, decrypt], source: measured}
          Cipher|NoKey:
            operations: {value: [encrypt, decrypt], source: measured}
    """.trimIndent()

    private val rest = """
        schemaVersion: 1
        family: mac.secret
        algorithms:
          Mac|HmacSHA256:
            key: {type: HMAC, origin: app, source: measured}
          Mac|AES-CMAC:
            key: {type: AES, origin: app, source: measured}
            operations: {value: [computeMac], source: measured}
          KeyAgreement|ECDH:
            key: {type: EC, origin: app, source: measured}
            operations: {value: [agree], source: measured}
    """.trimIndent()

    // P registers everything; Q lacks AES/OnlyP
    private val capability = object : DeviceCapability {
        override fun providers() = listOf("P", "Q")
        override fun check(provider: String, type: String, algorithm: String): Availability =
            if (provider == "Q" && algorithm == "AES/OnlyP") Availability.Unavailable("not_registered") else Availability.Available
    }

    private val uses = KeyUse(capability, KeyUse.parse(listOf(cipher, rest)))

    private fun picked(keyAlgorithm: String, consumer: String = "Q") =
        uses.of(keyAlgorithm, "P", consumer)?.let { "${it.type}|${it.algorithm} ${it.operation}" }

    @Test
    fun theFirstCatalogueEntryBothProvidersOfferWithATimedOperation() {
        assertEquals("Cipher|AES ENCRYPT", picked("AES"))
        assertEquals("Cipher|AES/OnlyP ENCRYPT", picked("AES", consumer = "P"))
        assertEquals("KeyAgreement|ECDH AGREE_KEY", picked("ec"))
        assertNull(picked("HmacSHA256"))
        assertNull(picked("RSA"))
    }

    @Test
    fun macWordsMapToTheTypesOperation() {
        val macOnly = KeyUse(capability, KeyUse.parse(listOf(rest)))
        assertEquals("COMPUTE_MAC", macOnly.of("AES", "P", "Q")?.operation?.name)
    }
}
