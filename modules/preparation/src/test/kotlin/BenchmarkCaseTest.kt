package io.github.junekim0007.cryptobench.preparation

import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.measurement.Operation
import io.github.junekim0007.cryptobench.preparation.measurement.Phase
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test

class BenchmarkCaseTest {

    /** Instrumentation records only method names, so the id must survive being one, and name every axis the case has. */
    @Test
    fun theIdIsSafeAsAMethodNameAndNamesEveryAxis() {
        val case = BenchmarkCase("Cipher", "AES/GCM/NoPadding", "AndroidOpenSSL", Operation.ENCRYPT, keySize = 256, inputSize = 1024)
        assertEquals("Cipher_AES-GCM-NoPadding_ENCRYPT_AndroidOpenSSL_k256_i1024_WARM", case.id)
        assertEquals("Cipher_AES-GCM-NoPadding_DECRYPT_AndroidOpenSSL_k256_i1024_WARM", case.copy(operation = Operation.DECRYPT).id)
        val keyGeneration = BenchmarkCase("KeyPairGenerator", "RSA", "AndroidOpenSSL", Operation.GENERATE_KEY_PAIR, keySize = 2048, phase = Phase.COLD)
        assertEquals("KeyPairGenerator_RSA_GENERATE-KEY-PAIR_AndroidOpenSSL_k2048_COLD", keyGeneration.id)
    }

    @Test
    fun rejectsWhatCannotBeMeasured() {
        assertEquals("missing_field: provider",
            assertThrows(IllegalArgumentException::class.java) { BenchmarkCase("Cipher", "AES", " ", Operation.ENCRYPT) }.message)
        assertEquals("not_positive: inputSize 0",
            assertThrows(IllegalArgumentException::class.java) { BenchmarkCase("Cipher", "AES", "SunJCE", Operation.ENCRYPT, inputSize = 0) }.message)
        assertEquals("missing_field: metrics",
            assertThrows(IllegalArgumentException::class.java) { BenchmarkCase("Cipher", "AES", "SunJCE", Operation.ENCRYPT, metrics = emptySet()) }.message)
    }

    /** Same primitive, different parameters: different measurements, so different names; stable across map order. */
    @Test
    fun parametersChangeTheIdDeterministically() {
        val oaepSha256 = mapOf("class" to "javax.crypto.spec.OAEPParameterSpec", "arguments" to listOf("SHA-256", "MGF1"))
        val plain = BenchmarkCase("Cipher", "RSA/ECB/OAEPPadding", "SunJCE", Operation.ENCRYPT, keySize = 2048, inputSize = 32)
        val tuned = plain.copy(parameters = oaepSha256)
        val reordered = plain.copy(parameters = linkedMapOf("arguments" to listOf("SHA-256", "MGF1"), "class" to "javax.crypto.spec.OAEPParameterSpec"))
        assertEquals("Cipher_RSA-ECB-OAEPPadding_ENCRYPT_SunJCE_k2048_i32_WARM", plain.id)
        assertTrue(tuned.id, tuned.id.matches(Regex("Cipher_RSA-ECB-OAEPPadding_ENCRYPT_SunJCE_k2048_i32_WARM_p[0-9a-f]{8}")))
        assertEquals(tuned.id, reordered.id)
    }

    /** Two groups of one primitive are two measurements, so the id names the group. */
    @Test
    fun theGroupIsPartOfTheName() {
        val case = BenchmarkCase("KeyPairGenerator", "EC", "SunEC", Operation.GENERATE_KEY_PAIR, group = "p256")
        assertEquals("KeyPairGenerator_EC-p256_GENERATE-KEY-PAIR_SunEC_WARM", case.id)
        assertEquals("KeyPairGenerator_EC_GENERATE-KEY-PAIR_SunEC_WARM", case.copy(group = "").id)
    }
}
