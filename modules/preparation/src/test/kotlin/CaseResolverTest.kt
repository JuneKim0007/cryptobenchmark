package io.github.junekim0007.cryptobench.preparation

import io.github.junekim0007.cryptobench.preparation.measurement.Operation
import io.github.junekim0007.cryptobench.preparation.measurement.Phase
import io.github.junekim0007.cryptobench.preparation.port.Availability
import io.github.junekim0007.cryptobench.preparation.port.DeviceCapability
import io.github.junekim0007.cryptobench.preparation.request.BenchmarkRequest
import io.github.junekim0007.cryptobench.preparation.request.Selection
import io.github.junekim0007.cryptobench.preparation.engine.EngineType
import io.github.junekim0007.cryptobench.preparation.engine.EngineTypes
import io.github.junekim0007.cryptobench.preparation.engine.KeyShape
import io.github.junekim0007.cryptobench.preparation.resolve.CaseResolver
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

    private fun request(vararg selections: Selection) = BenchmarkRequest(selections.toList(), EffectiveFixture.ONE_WARM_RUN)

    @Test
    fun expandsEveryAxisTheTypeIsMeasuredAlong() {
        val request = BenchmarkRequest(
            listOf(Selection("Cipher", "AES/GCM/NoPadding", keySizes = listOf(128, 256))),
            EffectiveFixture.ONE_WARM_RUN.copy(inputSizes = listOf(64, 1024), phases = setOf(Phase.WARM, Phase.COLD)),
        )
        val resolution = resolver.resolve(request)
        assertEquals(16, resolution.cases.size)
        assertEquals(setOf(Operation.ENCRYPT, Operation.DECRYPT), resolution.cases.map { it.operation }.toSet())
        assertEquals(emptyList<Any>(), resolution.rejections)
    }

    @Test
    fun digestsTakeNoKeyAndKeyGenerationTakesNoInput() {
        val resolution = resolver.resolve(request(
            Selection("MessageDigest", "SHA-256", keySizes = listOf(256)),
            Selection("KeyGenerator", "AES", keySizes = listOf(128, 256)),
        ))
        assertEquals(
            listOf(
                "MessageDigest_SHA-256_DIGEST_AndroidOpenSSL_i1024_WARM",
                "MessageDigest_SHA-256_DIGEST_BC_i1024_WARM",
                "KeyGenerator_AES_GENERATE-KEY_AndroidOpenSSL_k128_WARM",
                "KeyGenerator_AES_GENERATE-KEY_AndroidOpenSSL_k256_WARM",
            ),
            resolution.cases.map { it.id },
        )
    }

    /** Every unrunnable request is reported together, so one pass fixes the config. */
    @Test
    fun collectsEveryRejectionWithItsReason() {
        val resolution = resolver.resolve(request(
            Selection("Cipher", "AES/GCM/NoPadding", providers = listOf("AndroidOpenSSL", "BC", "SunJCE")),
            Selection("Cipher", "ChaCha20"),
        ))
        assertEquals(listOf("AndroidOpenSSL", "AndroidOpenSSL"), resolution.cases.map { it.provider })
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
        val digestAsKeyOnly = CaseResolver(device, EngineTypes.standard().with("messagedigest", EngineType(listOf(Operation.DIGEST), usesKeySize = true, usesInputSize = false, keyShape = KeyShape.NONE)))
        assertEquals(listOf(null, null), digestAsKeyOnly.resolve(request(Selection("MessageDigest", "SHA-256"))).cases.map { it.inputSize })
    }

    /** A parameter that cannot be built rejects its selection; nothing reaches a run. */
    @Test
    fun aBrokenParameterTreeRejectsTheSelection() {
        val broken = Selection("Cipher", "AES/GCM/NoPadding", parameters = mapOf("class" to "javax.crypto.spec.GCMParameterSpec", "arguments" to listOf(128)))
        val bothKeys = Selection("Cipher", "AES/GCM/NoPadding", keySizes = listOf(128),
            keyParameters = mapOf("class" to "java.security.spec.ECGenParameterSpec", "arguments" to listOf("secp256r1")))
        val fine = Selection("Cipher", "AES/GCM/NoPadding", parameters = mapOf("class" to "javax.crypto.spec.GCMParameterSpec", "arguments" to listOf(128, "fresh(12)")))
        val resolution = resolver.resolve(request(broken, bothKeys, fine))
        assertEquals(listOf(fine.parameters, fine.parameters), resolution.cases.map { it.parameters })
        assertEquals(
            listOf(
                "bind_failed: parameters: no constructor of javax.crypto.spec.GCMParameterSpec takes [Integer 128] (none with 1 arguments)",
                "key_parameters_and_key_sizes: set one; a key spec already fixes the size",
            ),
            resolution.rejections.map { it.reason },
        )
    }

    @Test
    fun aSelectionCanNarrowTheOperations() {
        val verifyOnly = Selection("Cipher", "AES/GCM/NoPadding", operations = setOf(Operation.DECRYPT))
        assertEquals(setOf(Operation.DECRYPT), resolver.resolve(request(verifyOnly)).cases.map { it.operation }.toSet())
    }

    /** Asking a digest to sign is a config mistake: rejected by name, with the operations that type does have. */
    @Test
    fun anOperationTheTypeDoesNotHaveIsRejected() {
        val wrong = Selection("MessageDigest", "SHA-256", operations = setOf(Operation.SIGN))
        assertEquals(listOf("unsupported_operation: [SIGN] for MessageDigest, one of [DIGEST]"),
            resolver.resolve(request(wrong)).rejections.map { it.reason })
    }
}
