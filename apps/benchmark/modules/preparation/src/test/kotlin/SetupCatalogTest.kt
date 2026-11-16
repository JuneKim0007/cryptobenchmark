package io.github.junekim0007.cryptobench.preparation

import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.measurement.Operation
import io.github.junekim0007.cryptobench.preparation.measurement.Variant
import io.github.junekim0007.cryptobench.preparation.operation.PerCall
import io.github.junekim0007.cryptobench.preparation.operation.SetupCatalog
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test

class SetupCatalogTest {

    private val catalog = SetupCatalog.standard

    private fun perCall(type: String, algorithm: String, variant: Variant = Variant.FIXED, hasIv: Boolean = false) =
        catalog.perCall(BenchmarkCase(type, algorithm, "P", Operation.TYPE_DEFAULT, variant = variant)) { hasIv }

    @Test
    fun fixedKeepsWhatEachEngineRowSays() {
        assertEquals(PerCall.OPERATION, perCall("MessageDigest", "SHA-256"))
        assertEquals(PerCall.OPERATION, perCall("Mac", "HmacSHA256"))
        assertEquals(PerCall.INIT_AND_OPERATION, perCall("Mac", "AES-GMAC"))
        assertEquals(PerCall.INIT_AND_OPERATION, perCall("Mac", "DSTU7624-128GMAC"))
        assertEquals(PerCall.OPERATION, perCall("Signature", "SHA256withECDSA"))
        assertEquals(PerCall.OPERATION, perCall("KeyAgreement", "ECDH"))
        assertEquals(PerCall.OPERATION, perCall("Cipher", "AES/ECB/PKCS5Padding"))
        assertEquals(PerCall.OPERATION, perCall("Cipher", "RSA/ECB/OAEPPadding"))
        assertEquals(PerCall.INIT_AND_OPERATION, perCall("Cipher", "AES/CBC/PKCS5Padding"))
        assertEquals(PerCall.INIT_AND_OPERATION, perCall("Cipher", "AES/CTR/NoPadding"))
        assertEquals(PerCall.INIT_AND_OPERATION, perCall("Cipher", "AES/GCM/NoPadding"))
        assertEquals(PerCall.INIT_AND_OPERATION, perCall("cipher", "aes/gcm/nopadding"))
    }

    @Test
    fun aCipherWithoutAModeIsDecidedByItsIv() {
        assertEquals(PerCall.OPERATION, perCall("Cipher", "ARCFOUR", hasIv = false))
        assertEquals(PerCall.INIT_AND_OPERATION, perCall("Cipher", "ChaCha20-Poly1305", hasIv = true))
        assertEquals(PerCall.INIT_AND_OPERATION, perCall("Cipher", "AES/XTS/NoPadding"))
    }

    @Test
    fun notFixedMakesEverythingPerCallAndKeyGenerationHasOneVariant() {
        for (type in listOf("MessageDigest", "Mac", "Signature", "KeyAgreement", "Cipher")) {
            assertEquals(type, PerCall.INSTANCE_INIT_AND_OPERATION, perCall(type, "A/ECB/B", Variant.NOT_FIXED))
        }
        val both = Variant.entries
        assertEquals(both to emptyList<Variant>(), catalog.paths("Cipher", both))
        assertEquals(listOf(Variant.NOT_FIXED) to emptyList<Variant>(), catalog.paths("Mac", listOf(Variant.NOT_FIXED)))
        for (generator in listOf("KeyGenerator", "KeyPairGenerator", "Unregistered")) {
            assertEquals(listOf(Variant.FIXED) to listOf(Variant.NOT_FIXED), catalog.paths(generator, both))
            assertEquals(listOf("fixed", "secure"), catalog.applicable(generator))
        }
        assertEquals(listOf("fixed", "notFixed"), catalog.applicable("Signature"))
        assertEquals(PerCall.OPERATION, perCall("KeyGenerator", "AES", Variant.NOT_FIXED))
    }

    @Test
    fun aGeneratorWhoseRowWouldRedoItsInitIsRefusedNotTimedInitOnce() {
        val two = SetupCatalog(mapOf("schemaVersion" to 1, "engines" to mapOf("KeyGenerator" to mapOf("fixed" to "operation"))))
        val case = BenchmarkCase("KeyGenerator", "AES", "P", Operation.GENERATE_KEY, variant = Variant.NOT_FIXED)
        val refused = assertThrows(IllegalArgumentException::class.java) { two.initOnce(case) }
        assertTrue(refused.message!!, refused.message!!.startsWith("not_supported: KeyGenerator"))
        assertEquals(PerCall.OPERATION, two.initOnce(case.copy(variant = Variant.FIXED)))
        assertEquals(PerCall.OPERATION, catalog.initOnce(case))
    }

    /** A row's `variants` names its paths; anything but distinct known names is refused, never guessed. */
    @Test
    fun aRowsVariantsListIsItsPaths() {
        fun row(variants: Any) = SetupCatalog(mapOf("schemaVersion" to 1, "engines" to mapOf("Mac" to mapOf("fixed" to "operation", "variants" to variants))))
        assertEquals(listOf("fixed"), row(listOf("fixed")).applicable("Mac"))
        assertEquals(PerCall.OPERATION, row(listOf("fixed")).perCall(BenchmarkCase("Mac", "HmacSHA256", "P", Operation.TYPE_DEFAULT, variant = Variant.NOT_FIXED)))
        for (bad in listOf(emptyList<String>(), listOf("fast"), listOf("fixed", "fixed"))) {
            val refused = assertThrows(IllegalArgumentException::class.java) { row(bad).applicable("Mac") }
            assertTrue(refused.message!!, refused.message!!.startsWith("invalid: setup-catalog.yaml engines.Mac.variants"))
        }
    }
}
