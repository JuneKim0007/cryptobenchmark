package io.github.junekim0007.cryptobench.discovery

import io.github.junekim0007.cryptobench.discovery.contract.ServiceTrialEntry
import io.github.junekim0007.cryptobench.discovery.contract.TransformationTrialEntry
import io.github.junekim0007.cryptobench.discovery.contract.TrialOutcome
import io.github.junekim0007.cryptobench.discovery.contract.TrialReport
import io.github.junekim0007.cryptobench.discovery.query.TransformationFailure
import io.github.junekim0007.cryptobench.discovery.query.TrialQuery
import org.junit.Assert.assertEquals
import org.junit.Test

class TrialQueryTest {

    private val query = TrialQuery(TrialReport(
        capturedAtMillis = 0L,
        services = listOf(
            ServiceTrialEntry("SunJCE", "Cipher", "AES", TrialOutcome.SUCCESS, listOf(
                TransformationTrialEntry("AES/CBC/NOPADDING", TrialOutcome.SUCCESS),
                TransformationTrialEntry("AES/CTR/PKCS5PADDING", TrialOutcome.failure("NoSuchPaddingException: CTR mode must be used with NoPadding")),
            )),
            ServiceTrialEntry("SunJCE", "Mac", "HmacSHA256", TrialOutcome.SUCCESS),
            ServiceTrialEntry("SunPKCS11", "KeyStore", "PKCS11", TrialOutcome.failure("provider_not_installed")),
        ),
    ))

    /** Lookups fold case the way the JCA does; transformations match in any spelling. */
    @Test
    fun findsOneTrialByName() {
        assertEquals("AES", query.serviceTrial("SunJCE", "cipher", "aes")?.algorithm)
        assertEquals(null, query.serviceTrial("SunJCE", "Cipher", "DES"))
        assertEquals(false, query.transformationTrial("SunJCE", "AES", "AES/CTR/PKCS5Padding")?.outcome?.instantiates)
        assertEquals(null, query.transformationTrial("SunJCE", "AES", "AES/GCM/NoPadding"))
    }

    @Test
    fun failingServices() {
        assertEquals(listOf("PKCS11"), query.failingServices().map { it.algorithm })
    }

    @Test
    fun failingTransformations() {
        assertEquals(
            listOf(TransformationFailure("SunJCE", "AES", "AES/CTR/PKCS5PADDING", "NoSuchPaddingException: CTR mode must be used with NoPadding")),
            query.failingTransformations(),
        )
    }

    @Test
    fun instantiationByProvider() {
        assertEquals(mapOf("SunJCE" to (2 to 2), "SunPKCS11" to (0 to 1)), query.instantiationByProvider())
    }
}
