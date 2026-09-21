package io.github.junekim0007.cryptobench.benchmark

import io.github.junekim0007.cryptobench.benchmark.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.benchmark.preparation.measurement.Phase
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Test

class BenchmarkCaseTest {

    /** Instrumentation records only method names, so the id must survive being one. */
    @Test
    fun theIdIsSafeAsAMethodNameAndNamesEveryAxis() {
        val case = BenchmarkCase("Cipher", "AES/GCM/NoPadding", "AndroidOpenSSL", keySize = 256, inputSize = 1024)
        assertEquals("Cipher_AES-GCM-NoPadding_AndroidOpenSSL_k256_i1024_WARM", case.id)
    }

    @Test
    fun keyGenerationHasNoInputSize() {
        val case = BenchmarkCase("KeyPairGenerator", "RSA", "AndroidOpenSSL", keySize = 2048, phase = Phase.COLD)
        assertEquals("KeyPairGenerator_RSA_AndroidOpenSSL_k2048_COLD", case.id)
    }

    @Test
    fun rejectsWhatCannotBeMeasured() {
        assertEquals("missing_field: provider",
            assertThrows(IllegalArgumentException::class.java) { BenchmarkCase("Cipher", "AES", " ") }.message)
        assertEquals("not_positive: inputSize 0",
            assertThrows(IllegalArgumentException::class.java) { BenchmarkCase("Cipher", "AES", "SunJCE", inputSize = 0) }.message)
        assertEquals("missing_field: metrics",
            assertThrows(IllegalArgumentException::class.java) { BenchmarkCase("Cipher", "AES", "SunJCE", metrics = emptySet()) }.message)
    }
}
