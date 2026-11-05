package io.github.junekim0007.cryptobench.discovery

import io.github.junekim0007.cryptobench.discovery.adapter.ProviderProbe
import io.github.junekim0007.cryptobench.discovery.contract.DefaultRunOutcome
import io.github.junekim0007.cryptobench.discovery.contract.TrialReport
import io.github.junekim0007.cryptobench.discovery.trial.DefaultRunTrial
import io.github.junekim0007.cryptobench.discovery.trial.TrialRunner
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test
import java.security.Security

/** Against the live JVM. Instantiating is not running: these are the cases where the two differ. */
class DefaultRunTrialTest {

    private fun service(provider: String, type: String, algorithm: String): DefaultRunOutcome? =
        REPORT.services.single { it.provider == provider && it.type == type && it.algorithm == algorithm }.defaultRun

    private fun transformation(provider: String, algorithm: String, name: String): DefaultRunOutcome? =
        REPORT.services.single { it.provider == provider && it.type == "Cipher" && it.algorithm == algorithm }
            .transformations.single { it.name.equals(name, ignoreCase = true) }.defaultRun

    @Test
    fun recordsTheKeyAndWhatTheProviderChose() {
        assertEquals("the report says which input size a default run starts from", 1024, REPORT.defaultRunInputSize)
        val gcm = service("SunJCE", "Cipher", "AES/GCM/NoPadding")!!
        assertTrue(gcm.works)
        assertEquals("AES", gcm.keyAlgorithm)
        assertEquals("ivBytes=12 tagBits=128", gcm.providerChose)
        assertEquals(1024, gcm.inputSize)
        assertTrue(service("SunJCE", "Cipher", "AES")!!.bareName)
        assertEquals(128, service("SunJCE", "Cipher", "AES_128/GCM/NoPadding")!!.keySize)
    }

    /** A key-wrap integrity check value is the same on every init, so it is not reported as an IV; a CBC IV changes. */
    @Test
    fun aConstantTheProviderFillsInIsNotAnIv() {
        val wrap = service("SunJCE", "Cipher", "AES/KWP/NoPadding")!!
        assertTrue(wrap.error, wrap.works)
        assertEquals("fixedValueBytes=4", wrap.providerChose)
        assertEquals("ivBytes=16", transformation("SunJCE", "AES", "AES/CBC/NoPadding")!!.providerChose)
    }

    /** RSA cannot encrypt 1024 bytes; the smaller size is tried and recorded instead of failing the entry. */
    @Test
    fun anInputLimitIsRecordedAsTheSizeThatWorked() {
        val oaep = transformation("SunJCE", "RSA", "RSA/ECB/OAEPPadding")!!
        assertTrue(oaep.error, oaep.works)
        assertEquals(32, oaep.inputSize)
        assertEquals("digest=SHA-1 mgf1=SHA-1 labelBytes=0", oaep.providerChose)
    }

    @Test
    fun generatorsRecordTheProviderDefaultSize() {
        val sizes = listOf(
            service("SunJCE", "KeyGenerator", "AES"),
            service("SunRsaSign", "KeyPairGenerator", "RSA"),
            service("SunEC", "KeyPairGenerator", "EC"),
        ).map { it!!.keySize }
        assertTrue("defaults not recorded: $sizes", sizes.all { it != null && it > 0 })
        assertNull(service("SunEC", "KeyPairGenerator", "Ed25519")!!.keySize)
    }

    @Test
    fun generatorsRecordTheirKeysFormatAndAPairItsPrivateKeys() {
        assertEquals("RAW", service("SunJCE", "KeyGenerator", "AES")!!.keyFormat)
        assertEquals("PKCS#8", service("SunRsaSign", "KeyPairGenerator", "RSA")!!.keyFormat)
        assertEquals("", service("SunJCE", "Mac", "HmacSHA256")!!.keyFormat)
    }

    @Test
    fun instantiatesButDoesNotRun() {
        listOf(
            service("SunJCE", "KeyGenerator", "SunTlsPrf"),
            service("SunRsaSign", "Signature", "RSASSA-PSS"),
            service("SUN", "Signature", "NONEwithDSA"),
            service("SunJCE", "Mac", "HmacPBESHA256"),
        ).forEach { outcome ->
            assertFalse("expected a failure: $outcome", outcome!!.works)
            assertTrue(outcome.error.isNotEmpty())
        }
    }

    @Test
    fun agreementsAndSignaturesRun() {
        assertTrue(service("SunEC", "KeyAgreement", "ECDH")!!.works)
        assertTrue(service("SunEC", "KeyAgreement", "X25519")!!.works)
        assertEquals("EC", service("SunEC", "Signature", "SHA256withECDSA")!!.keyAlgorithm)
    }

    /** No call is registered for the type, so no default run is claimed. */
    @Test
    fun typesWithoutACallGetNoDefaultRun() {
        assertNull(service("SunJCE", "AlgorithmParameters", "AES"))
    }

    companion object {
        private val REPORT: TrialReport by lazy {
            val providers = Security.getProviders()
            DefaultRunTrial().run(TrialRunner().run(ProviderProbe().capture(providers), providers), providers)
        }
    }
}
