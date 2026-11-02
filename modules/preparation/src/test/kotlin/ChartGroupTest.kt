package io.github.junekim0007.cryptobench.preparation

import io.github.junekim0007.cryptobench.preparation.input.OperationInput
import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterial
import io.github.junekim0007.cryptobench.preparation.key.plan.KeyRecipe
import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.measurement.Operation
import io.github.junekim0007.cryptobench.preparation.prepare.ChartGroup
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase
import org.junit.Assert.assertEquals
import org.junit.Test

class ChartGroupTest {

    private val none = KeyRecipe.None
    private val secret = KeyRecipe.Secret("AES", 128, "SunJCE")
    private val pair = KeyRecipe.Pair("RSA", 2048, "SunRsaSign")

    @Test
    fun theServiceTypeDecides() {
        assertEquals(ChartGroup.SIGNATURE, ChartGroup.of("Signature", pair))
        assertEquals(ChartGroup.SIGNATURE, ChartGroup.of("signature", pair))
        assertEquals(ChartGroup.MAC, ChartGroup.of("Mac", secret))
        assertEquals(ChartGroup.HASH, ChartGroup.of("MessageDigest", none))
        assertEquals(ChartGroup.KEYGEN_ASYMMETRIC, ChartGroup.of("KeyPairGenerator", none))
        assertEquals(ChartGroup.KEYGEN_SYMMETRIC, ChartGroup.of("KeyGenerator", none))
    }

    @Test
    fun theKeyKindSplitsCipherOnly() {
        assertEquals(ChartGroup.SYMMETRIC_CIPHER, ChartGroup.of("Cipher", secret))
        assertEquals(ChartGroup.ASYMMETRIC_CIPHER, ChartGroup.of("cipher", pair))
        assertEquals(ChartGroup.UNIDENTIFIED, ChartGroup.of("Cipher", none))
    }

    @Test
    fun whatItCannotPlaceIsGroupZero() {
        assertEquals(0, ChartGroup.of("SecretKeyFactory", none).id)
        assertEquals(ChartGroup.UNIDENTIFIED, ChartGroup.of("KeyStore", none))
    }

    @Test
    fun idsAreUniqueAndZeroIsUnidentified() {
        assertEquals(ChartGroup.entries.size, ChartGroup.entries.map { it.id }.toSet().size)
        assertEquals(ChartGroup.UNIDENTIFIED, ChartGroup.entries.single { it.id == 0 })
    }

    @Test
    fun aCaseKnowsItsGroup() {
        val case = BenchmarkCase("Mac", "HmacSHA256", "SunJCE", Operation.COMPUTE_MAC, inputSize = 64)
        assertEquals("mac", PreparedCase(case, secret, KeyMaterial.None, null, null, OperationInput.None).chartGroup.label)
    }
}
