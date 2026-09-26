package io.github.junekim0007.cryptobench.benchmark

import io.github.junekim0007.cryptobench.benchmark.report.BenchmarkJson
import io.github.junekim0007.cryptobench.benchmark.report.JetpackResults
import org.junit.Assert.assertEquals
import org.junit.Test
import java.io.File

/**
 * Jetpack's output says how long a name took; it does not say what the name was measuring. What a
 * case is comes from the prepared.yaml written on the same device, joined on the case id.
 */
class JetpackResultsTest {

    private val example = File("example")

    private val converted = JetpackResults.convert(
        File(example, "benchmark_jetpack_example.json").readText(),
        File(example, "benchmark_prepared_example.yaml").readText(),
    )

    @Test
    fun aCaseKeepsItsSamplesAndGetsItsShapeFromThePlan() {
        val digest = converted.rows.single { it.algorithm == "SHA-256" }
        assertEquals("MessageDigest", digest.type)
        assertEquals("AndroidOpenSSL", digest.provider)
        assertEquals("DIGEST", digest.operation)
        assertEquals(null, digest.keySize)
        assertEquals(1024, digest.inputSize)
        assertEquals(8192, digest.iterations)
        assertEquals(listOf(1191L, 1180L, 1256L, 1188L, 1193L), digest.nanosPerOperation)
        val encrypt = converted.rows.single { it.algorithm == "AES/GCM/NoPadding" }
        assertEquals(128, encrypt.keySize)
        assertEquals(4096, encrypt.iterations)
    }

    /** A measurement with no case in the plan is named, not guessed at: the two files disagree. */
    @Test
    fun aMeasurementWithNoCaseIsReported() {
        assertEquals(listOf("Cipher_ChaCha20_ENCRYPT_AndroidOpenSSL_k256_i1024_WARM"), converted.missing)
        assertEquals(2, converted.rows.size)
    }

    /** Whether the clocks were locked and whether the device throttled decide if the numbers count. */
    @Test
    fun theRuntimeCarriesWhatMakesTheNumbersJudgeable() {
        assertEquals(
            mapOf(
                "model" to "Pixel 9",
                "fingerprint" to "google/tokay/tokay:16/BP3A.250905.014/13718934:user/release-keys",
                "sdkInt" to "36",
                "cpuLocked" to "false",
                "sustainedPerformanceModeEnabled" to "true",
                "compilationMode" to "DEFAULT",
                "thermalThrottleSleepSeconds" to "90",
            ),
            converted.runtime,
        )
    }

    @Test
    fun theConvertedFileIsWhatTheAnalysisReads() {
        val text = BenchmarkJson(example).text(converted.runtime, converted.rows)
        assertEquals(
            """{
  "runtime": {"model": "Pixel 9", "fingerprint": "google/tokay/tokay:16/BP3A.250905.014/13718934:user/release-keys", "sdkInt": "36", "cpuLocked": "false", "sustainedPerformanceModeEnabled": "true", "compilationMode": "DEFAULT", "thermalThrottleSleepSeconds": "90"},
  "cases": [
    {"id": "MessageDigest_SHA-256_DIGEST_AndroidOpenSSL_i1024_WARM", "type": "MessageDigest", "algorithm": "SHA-256", "provider": "AndroidOpenSSL", "operation": "DIGEST", "keySize": null, "inputSize": 1024, "iterations": 8192, "nanosPerOperation": [1191, 1180, 1256, 1188, 1193]},
    {"id": "Cipher_AES-GCM-NoPadding_ENCRYPT_AndroidOpenSSL_k128_i1024_WARM_p81667fe4", "type": "Cipher", "algorithm": "AES/GCM/NoPadding", "provider": "AndroidOpenSSL", "operation": "ENCRYPT", "keySize": 128, "inputSize": 1024, "iterations": 4096, "nanosPerOperation": [2401, 2380, 2611, 2396, 2410]}
  ]
}
""",
            text,
        )
    }
}
