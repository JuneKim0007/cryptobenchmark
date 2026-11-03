package io.github.junekim0007.cryptobench.preparation

import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.measurement.Operation
import io.github.junekim0007.cryptobench.preparation.measurement.Variant
import io.github.junekim0007.cryptobench.preparation.operation.PerCall
import io.github.junekim0007.cryptobench.preparation.operation.SetupCatalog
import org.junit.Assert.assertEquals
import org.junit.Test

class SetupCatalogTest {

    private val catalog = SetupCatalog.standard

    private fun perCall(type: String, algorithm: String, variant: Variant = Variant.FIXED, hasIv: Boolean = false) =
        catalog.perCall(BenchmarkCase(type, algorithm, "P", Operation.TYPE_DEFAULT, variant = variant)) { hasIv }

    @Test
    fun fixedKeepsWhatEachEngineRowSays() {
        assertEquals(PerCall.OPERATION, perCall("MessageDigest", "SHA-256"))
        assertEquals(PerCall.OPERATION, perCall("Mac", "HmacSHA256"))
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
        assertEquals(both, catalog.variantsOf("Cipher", both))
        assertEquals(listOf(Variant.NOT_FIXED), catalog.variantsOf("Mac", listOf(Variant.NOT_FIXED)))
        assertEquals(listOf(Variant.FIXED), catalog.variantsOf("KeyGenerator", both))
        assertEquals(listOf(Variant.FIXED), catalog.variantsOf("KeyPairGenerator", both))
        assertEquals(listOf(Variant.FIXED), catalog.variantsOf("Unregistered", both))
        assertEquals(PerCall.OPERATION, perCall("KeyGenerator", "AES", Variant.NOT_FIXED))
    }
}
