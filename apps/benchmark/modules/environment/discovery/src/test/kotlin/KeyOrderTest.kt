package io.github.junekim0007.cryptobench.discovery.trial.call

import io.github.junekim0007.cryptobench.document.catalogue.FamilyCatalogue
import org.junit.Assert.assertEquals
import org.junit.Test
import java.security.Provider
import java.security.SecureRandom
import java.security.Security
import java.security.spec.AlgorithmParameterSpec
import javax.crypto.KeyGeneratorSpi
import javax.crypto.SecretKey
import javax.crypto.spec.SecretKeySpec

/** Every candidate on the service's own provider before another provider's: a later name it makes beats an earlier one only another makes. */
class KeyOrderTest {

    @Test
    fun thePreferredProviderTriesEveryCandidateFirst() {
        val own = Security.getProvider("SunJCE")
        val keys = DefaultKeys(listOf(own, Other()), KeyCandidates(FamilyCatalogue(emptyList()), null, emptyList()))
        val (secret, _) = keys.firstSecret(own, listOf(KeyCandidates.Candidate("ONLYOTHER"), KeyCandidates.Candidate("AES"))).getOrThrow()
        assertEquals("SunJCE" to "AES", secret.provider to secret.algorithm)
        val (elsewhere, _) = keys.firstSecret(own, listOf(KeyCandidates.Candidate("ONLYOTHER"))).getOrThrow()
        assertEquals("Other", elsewhere.provider)
    }

    class OtherGenerator : KeyGeneratorSpi() {
        override fun engineInit(random: SecureRandom?) = Unit
        override fun engineInit(params: AlgorithmParameterSpec?, random: SecureRandom?) = Unit
        override fun engineInit(keysize: Int, random: SecureRandom?) = Unit
        override fun engineGenerateKey(): SecretKey = SecretKeySpec(ByteArray(16), "ONLYOTHER")
    }

    private class Other : Provider("Other", 1.0, "a generator only it has") {
        init { put("KeyGenerator.ONLYOTHER", OtherGenerator::class.java.name) }
    }
}
