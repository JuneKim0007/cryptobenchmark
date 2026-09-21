package io.github.junekim0007.cryptobench.benchmark

import io.github.junekim0007.cryptobench.benchmark.preparation.measurement.Phase
import io.github.junekim0007.cryptobench.benchmark.preparation.port.Availability
import io.github.junekim0007.cryptobench.benchmark.preparation.port.DeviceCapability
import io.github.junekim0007.cryptobench.benchmark.preparation.request.BenchmarkRequest
import io.github.junekim0007.cryptobench.benchmark.preparation.request.Selection
import io.github.junekim0007.cryptobench.benchmark.preparation.resolve.AxisRule
import io.github.junekim0007.cryptobench.benchmark.preparation.resolve.AxisRules
import io.github.junekim0007.cryptobench.benchmark.preparation.resolve.CaseResolver
import org.junit.Assert.assertEquals
import org.junit.Test

class CaseResolverTest {

    /** The resolver only sees the port, so a map is a whole device. */
    private val device = object : DeviceCapability {
        private val serves = mapOf(
            "AndroidOpenSSL" to setOf("Cipher/AES/GCM/NoPadding", "MessageDigest/SHA-256", "KeyGenerator/AES"),
            "BC" to setOf("MessageDigest/SHA-256"),
        )

        override fun providers(): List<String> = listOf("AndroidOpenSSL", "BC")

        override fun check(provider: String, type: String, algorithm: String): Availability = when {
            provider !in serves -> Availability.Unavailable("provider_not_installed")
            "$type/$algorithm" in serves.getValue(provider) -> Availability.Available
            else -> Availability.Unavailable("not_registered")
        }
    }

    private val resolver = CaseResolver(device)

    @Test
    fun expandsEveryAxisTheTypeIsMeasuredAlong() {
        val request = BenchmarkRequest(
            listOf(Selection("Cipher", "AES/GCM/NoPadding", keySizes = listOf(128, 256))),
            inputSizes = listOf(64, 1024),
            phases = setOf(Phase.WARM, Phase.COLD),
        )
        val resolution = resolver.resolve(request)
        assertEquals(8, resolution.cases.size)
        assertEquals(emptyList<Any>(), resolution.rejections)
    }

    @Test
    fun digestsTakeNoKeyAndKeyGenerationTakesNoInput() {
        val resolution = resolver.resolve(BenchmarkRequest(listOf(
            Selection("MessageDigest", "SHA-256", keySizes = listOf(256)),
            Selection("KeyGenerator", "AES", keySizes = listOf(128, 256)),
        )))
        assertEquals(
            listOf(
                "MessageDigest_SHA-256_AndroidOpenSSL_i1024_WARM",
                "MessageDigest_SHA-256_BC_i1024_WARM",
                "KeyGenerator_AES_AndroidOpenSSL_k128_WARM",
                "KeyGenerator_AES_AndroidOpenSSL_k256_WARM",
            ),
            resolution.cases.map { it.id },
        )
    }

    /** Every unrunnable request is reported together, so one pass fixes the config. */
    @Test
    fun collectsEveryRejectionWithItsReason() {
        val resolution = resolver.resolve(BenchmarkRequest(listOf(
            Selection("Cipher", "AES/GCM/NoPadding", providers = listOf("AndroidOpenSSL", "BC", "SunJCE")),
            Selection("Cipher", "ChaCha20"),
        )))
        assertEquals(listOf("AndroidOpenSSL"), resolution.cases.map { it.provider })
        assertEquals(
            listOf(
                "Cipher/AES/GCM/NoPadding@BC: not_registered",
                "Cipher/AES/GCM/NoPadding@SunJCE: provider_not_installed",
                "Cipher/ChaCha20@*: no_provider",
            ),
            resolution.rejections.map { it.toString() },
        )
    }

    @Test
    fun anUnregisteredTypeResolvesUnderTheFallbackAndCanBeRegistered() {
        val request = BenchmarkRequest(listOf(Selection("MessageDigest", "SHA-256")))
        val digestAsKeyOnly = CaseResolver(device, AxisRules.standard().with("messagedigest", AxisRule(usesKeySize = true, usesInputSize = false)))
        assertEquals(listOf(null, null), digestAsKeyOnly.resolve(request).cases.map { it.inputSize })
    }
}
