package io.github.junekim0007.cryptobench.discovery

import io.github.junekim0007.cryptobench.discovery.trial.call.CipherCall
import io.github.junekim0007.cryptobench.discovery.contract.ParameterReadBack
import org.junit.Assert.assertEquals
import org.junit.Test
import java.security.KeyPairGenerator
import java.security.spec.MGF1ParameterSpec
import java.security.spec.PSSParameterSpec
import javax.crypto.Cipher
import javax.crypto.spec.OAEPParameterSpec
import javax.crypto.spec.PSource

/** Levels 2 and 3 read a provider's parameters back through one describe, with preparation's field names. */
class ParameterReadBackTest {

    @Test
    fun aPssSpecRecordsItsMgf1DigestBesideTheSalt() {
        val pss = PSSParameterSpec("SHA-256", "MGF1", MGF1ParameterSpec.SHA384, 32, 1)
        assertEquals(mapOf("class" to "PSSParameterSpec", "digest" to "SHA-256", "mgf1" to "SHA-384", "saltBytes" to 32), ParameterReadBack.describe(pss))
    }

    @Test
    fun theDefaultRunsProviderChoseIsLevelThreesReadBack() {
        val cipher = Cipher.getInstance("RSA/ECB/OAEPPadding", "SunJCE")
        val key = KeyPairGenerator.getInstance("RSA").apply { initialize(2048) }.generateKeyPair().public
        cipher.init(Cipher.ENCRYPT_MODE, key, OAEPParameterSpec("SHA-256", "MGF1", MGF1ParameterSpec.SHA1, PSource.PSpecified(ByteArray(3))))
        val described = ParameterReadBack.describe(ParameterReadBack.readable(cipher.parameters)!!) - "class"
        assertEquals(described.entries.joinToString(" ") { "${it.key}=${it.value}" }, CipherCall.chosenParameters(cipher, key))
        assertEquals("digest=SHA-256 mgf1=SHA-1 labelBytes=3", CipherCall.chosenParameters(cipher, key))
    }
}
