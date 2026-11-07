package io.github.junekim0007.cryptobench.discovery

import io.github.junekim0007.cryptobench.discovery.adapter.ProviderProbe
import io.github.junekim0007.cryptobench.discovery.contract.ServiceRequirement
import io.github.junekim0007.cryptobench.discovery.trial.DefaultRunTrial
import io.github.junekim0007.cryptobench.discovery.trial.TrialRunner
import io.github.junekim0007.cryptobench.discovery.trial.call.DefaultKeys
import io.github.junekim0007.cryptobench.discovery.trial.requirement.RequirementTrial
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Test
import java.security.Security

/** The reset test against the live JVM's providers: a second call per direction, and the calls it ran. */
class ResetRunTest {

    private fun service(type: String, algorithm: String, provider: String): ServiceRequirement =
        REPORT.services.single { it.provider == provider && it.type == type && it.algorithm.equals(algorithm, ignoreCase = true) }

    @Suppress("UNCHECKED_CAST")
    private fun reset(service: ServiceRequirement, direction: String): Map<String, Any> =
        (service.facts.getValue("reset") as Map<String, Any>).getValue(direction) as Map<String, Any>

    @Test
    fun aDeterministicCipherResetsBothWays() {
        val cbc = service("Cipher", "AES/CBC/PKCS5Padding", "SunJCE")
        assertEquals(true, reset(cbc, "forward")["resets"])
        assertEquals("same", reset(cbc, "forward")["output"])
        assertEquals(true, reset(cbc, "reverse")["resets"])
        assertEquals(mapOf("setup" to listOf("init"), "operation" to listOf("update", "doFinal")), reset(cbc, "forward")["calls"])
    }

    @Test
    fun aNonceAeadRefusesTheSecondEncryptWithItsClassAndDecryptDoesNot() {
        val gcm = service("Cipher", "AES/GCM/NoPadding", "SunJCE")
        assertEquals(false, reset(gcm, "forward")["resets"])
        assertEquals("IllegalStateException", reset(gcm, "forward")["refusedBy"])
        assertEquals(true, reset(gcm, "reverse")["resets"])
        assertEquals(mapOf("setup" to listOf("init"), "operation" to listOf("updateAAD", "update", "doFinal")), reset(gcm, "reverse")["calls"])
    }

    @Test
    fun aRandomizedResultResetsWhenTheSecondOneReverses() {
        val pkcs1 = service("Signature", "SHA256withRSA", "SunRsaSign")
        assertEquals(true, reset(pkcs1, "forward")["resets"])
        val ecdsa = service("Signature", "SHA256withECDSA", "SunEC")
        assertEquals("randomized", reset(ecdsa, "forward")["output"])
        assertEquals(true, reset(ecdsa, "forward")["resets"])
        assertEquals(listOf("initVerify"), (reset(ecdsa, "reverse")["calls"] as Map<*, *>)["setup"])
    }

    @Test
    fun anAgreementSaysWhetherDoPhaseRepeats() {
        val ecdh = reset(service("KeyAgreement", "ECDH", "SunEC"), "forward")
        assertEquals(mapOf("setup" to listOf("init"), "operation" to listOf("doPhase", "generateSecret")), ecdh["calls"])
        assertNotNull(ecdh["withoutDoPhase"])
    }

    @Test
    fun aDigestMacAndGeneratorEachRunTwice() {
        assertEquals(mapOf("setup" to emptyList<String>(), "operation" to listOf("update", "digest")), reset(service("MessageDigest", "SHA-256", "SUN"), "forward")["calls"])
        assertEquals(true, reset(service("MessageDigest", "SHA-256", "SUN"), "forward")["resets"])
        assertEquals(true, reset(service("Mac", "HmacSHA256", "SunJCE"), "forward")["resets"])
        assertEquals("not_compared", reset(service("KeyGenerator", "AES", "SunJCE"), "forward")["output"])
    }

    @Test
    fun everyRunnableServiceOfACalledTypeHoldsAResetRow() {
        val runnable = REPORT.services.filter { it.status == ServiceRequirement.RUNNABLE && it.type in setOf("Cipher", "Mac", "Signature", "MessageDigest", "KeyGenerator", "KeyPairGenerator", "KeyAgreement") }
        assertTrue(runnable.isNotEmpty())
        assertEquals(emptyList<String>(), runnable.filter { "reset" !in it.facts }.map { it.provider + " " + it.algorithm })
    }

    private companion object {
        val REPORT by lazy {
            val providers = Security.getProviders()
            val capture = ProviderProbe().capture(providers)
            val keys = DefaultKeys(providers.toList())
            RequirementTrial().run(capture, DefaultRunTrial().run(TrialRunner().run(capture, providers), providers, keys), providers, keys)
        }
    }
}
