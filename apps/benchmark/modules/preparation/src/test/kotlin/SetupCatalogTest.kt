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

    private fun measured(type: String, algorithm: String, provider: String, platform: String?) =
        catalog.perCall(BenchmarkCase(type, algorithm, provider, Operation.TYPE_DEFAULT), platform) { false }

    @Test
    fun aCataloguedCipherOrMacTakesInitIntoTheCallWhenItsBuildAsksAFreshInitValueOrRefusesASecondOperation() {
        assertEquals(PerCall.INIT_AND_OPERATION, measured("Mac", "POLY1305-AES", "BundledBC", "jdk-25"))
        assertEquals(PerCall.INIT_AND_OPERATION, measured("Mac", "AESCCMMAC", "BundledBC", "jdk-25"))
        assertEquals(PerCall.OPERATION, measured("Mac", "HmacSHA256", "SunJCE", "jdk-25"))
        assertEquals(PerCall.OPERATION, measured("Cipher", "AES/KW/NoPadding", "SunJCE", "jdk-25"))
        assertEquals(PerCall.INIT_AND_OPERATION, measured("Cipher", "AES/GCM/NoPadding", "SunJCE", "jdk-25"))
        assertEquals(PerCall.INIT_AND_OPERATION, measured("Cipher", "ChaCha20", "SunJCE", "jdk-25"))
        assertEquals(PerCall.INIT_AND_OPERATION, measured("Cipher", "PBEWithHmacSHA256AndAES_128", "AndroidOpenSSL", "android-33"))
        assertEquals(PerCall.INIT_AND_OPERATION, measured("Cipher", "AES/GCM-SIV/NoPadding", "AndroidOpenSSL", "android-33"))
    }

    @Test
    fun anUncataloguedNameOrAProviderWithNoMeasuredBuildKeepsTheRow() {
        assertEquals(PerCall.OPERATION, measured("Mac", "POLY1305-AES", "Unmeasured", "jdk-25"))
        assertEquals(PerCall.INIT_AND_OPERATION, measured("Cipher", "NoSuchCipher/CBC/NoPadding", "SunJCE", "jdk-25"))
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
        val both = listOf(Variant.FIXED, Variant.NOT_FIXED)
        assertEquals(both to emptyList<Variant>(), catalog.paths("Cipher", both))
        assertEquals(listOf(Variant.NOT_FIXED) to emptyList<Variant>(), catalog.paths("Mac", listOf(Variant.NOT_FIXED)))
        for (generator in listOf("KeyGenerator", "KeyPairGenerator")) {
            assertEquals(listOf(Variant.FIXED) to listOf(Variant.NOT_FIXED), catalog.paths(generator, both))
        }
        assertEquals(emptyList<Variant>() to both, catalog.paths("Unregistered", both))
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
    /** A row whose variants hold no notFixed makes its instance once: the call is the operation alone. */
    @Test
    fun aRowWithoutNotFixedTimesTheOperationAlone() {
        val row = SetupCatalog(mapOf("schemaVersion" to 1, "engines" to mapOf("Mac" to mapOf("fixed" to "operation", "variants" to listOf("fixed")))))
        assertEquals(PerCall.OPERATION, row.perCall(BenchmarkCase("Mac", "HmacSHA256", "P", Operation.TYPE_DEFAULT, variant = Variant.NOT_FIXED)))
    }
}
