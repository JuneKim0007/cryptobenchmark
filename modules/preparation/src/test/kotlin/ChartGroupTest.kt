package io.github.junekim0007.cryptobench.preparation

import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.measurement.ChartGroup
import io.github.junekim0007.cryptobench.preparation.measurement.Operation
import org.junit.Assert.assertEquals
import org.junit.Test

class ChartGroupTest {

    /** The names that mislead a keyword match: the service type must win over SHA or RSA inside the name. */
    @Test
    fun theServiceTypeDecidesNotTheKeyword() {
        assertEquals(ChartGroup.SIGNATURE, ChartGroup.of("Signature", "SHA256withRSA"))
        assertEquals(ChartGroup.SIGNATURE, ChartGroup.of("Signature", "SHA256withECDSA"))
        assertEquals(ChartGroup.MAC, ChartGroup.of("Mac", "HmacSHA256"))
        assertEquals(ChartGroup.HASH, ChartGroup.of("MessageDigest", "SHA-256"))
        assertEquals(ChartGroup.KEYGEN_ASYMMETRIC, ChartGroup.of("KeyPairGenerator", "RSA"))
        assertEquals(ChartGroup.KEYGEN_SYMMETRIC, ChartGroup.of("KeyGenerator", "AES"))
    }

    /** Cipher covers both kinds, so only there does the name split them. */
    @Test
    fun theNameSplitsCipherOnly() {
        assertEquals(ChartGroup.SYMMETRIC_CIPHER, ChartGroup.of("Cipher", "AES/GCM/NoPadding"))
        assertEquals(ChartGroup.SYMMETRIC_CIPHER, ChartGroup.of("Cipher", "ChaCha20/Poly1305/NoPadding"))
        assertEquals(ChartGroup.SYMMETRIC_CIPHER, ChartGroup.of("Cipher", "DESEDE/CBC/PKCS5Padding"))
        assertEquals(ChartGroup.ASYMMETRIC_CIPHER, ChartGroup.of("Cipher", "RSA/ECB/OAEPWithSHA-256AndMGF1Padding"))
        assertEquals(ChartGroup.ASYMMETRIC_CIPHER, ChartGroup.of("Cipher", "rsa/ecb/pkcs1padding"))
    }

    @Test
    fun whatItCannotPlaceIsGroupZero() {
        assertEquals(0, ChartGroup.of("SecretKeyFactory", "PBKDF2WithHmacSHA1").id)
        assertEquals(ChartGroup.UNIDENTIFIED, ChartGroup.of("KeyStore", "AndroidKeyStore"))
    }

    @Test
    fun idsAreUniqueAndZeroIsUnidentified() {
        assertEquals(ChartGroup.entries.size, ChartGroup.entries.map { it.id }.toSet().size)
        assertEquals(ChartGroup.UNIDENTIFIED, ChartGroup.entries.single { it.id == 0 })
    }

    @Test
    fun aCaseKnowsItsGroup() {
        val case = BenchmarkCase("Mac", "HmacSHA256", "SunJCE", Operation.COMPUTE_MAC, inputSize = 64)
        assertEquals("mac", case.chartGroup.label)
    }
}
