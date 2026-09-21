package io.github.junekim0007.cryptobench.benchmark

import io.github.junekim0007.cryptobench.benchmark.preparation.adapter.DiscoveryCapability
import io.github.junekim0007.cryptobench.benchmark.preparation.port.Availability
import io.github.junekim0007.cryptobench.discovery.adapter.ProviderProbe
import io.github.junekim0007.cryptobench.discovery.trial.TrialRunner
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test
import java.security.Security

/** Against the live JVM: what the adapter answers is what the trial saw, not what the provider declared. */
class DiscoveryCapabilityTest {

    private val capture = ProviderProbe().capture(Security.getProviders())
    private val capability = DiscoveryCapability(capture, TrialRunner().run(capture, Security.getProviders()))

    private fun reason(provider: String, type: String, algorithm: String): String =
        when (val availability = capability.check(provider, type, algorithm)) {
            Availability.Available -> "available"
            is Availability.Unavailable -> availability.reason
        }

    @Test
    fun registeredNamesAliasesAndComposedTransformations() {
        assertEquals("available", reason("SunJCE", "Cipher", "AES/GCM/NoPadding"))
        assertEquals("available", reason("SunJCE", "Cipher", "AES/CBC/PKCS5Padding"))
        assertEquals("available", reason("SunRsaSign", "Signature", "1.2.840.113549.1.1.11"))
    }

    @Test
    fun declaredButRefusedIsNotAvailable() {
        assertTrue(reason("SunJCE", "Cipher", "AES/CTR/PKCS5Padding").startsWith("transformation_fails: NoSuchPaddingException"))
    }

    @Test
    fun namesWhyAnythingElseIsUnavailable() {
        assertEquals("provider_not_installed", reason("AndroidOpenSSL", "Cipher", "AES"))
        assertEquals("not_registered", reason("SunJCE", "Cipher", "Serpent"))
        assertEquals("not_registered", reason("SunJCE", "Cipher", "Serpent/CBC/NoPadding"))
        assertEquals("not_tried", reason("SunJCE", "Cipher", "AES/XTS/NoPadding"))
    }

    @Test
    fun providersComeInPrecedenceOrder() {
        assertEquals(Security.getProviders().map { it.name }, capability.providers())
    }

    /** A trial describes one capture; pairing it with another would answer for a different device state. */
    @Test
    fun refusesATrialOfAnotherCapture() {
        val other = ProviderProbe().capture(Security.getProviders(), capturedAtMillis = capture.capturedAtMillis + 1)
        val error = assertThrows(IllegalArgumentException::class.java) {
            DiscoveryCapability(other, TrialRunner().run(capture, Security.getProviders()))
        }
        assertTrue(error.message!!.startsWith("mismatched_trial"))
    }
}
