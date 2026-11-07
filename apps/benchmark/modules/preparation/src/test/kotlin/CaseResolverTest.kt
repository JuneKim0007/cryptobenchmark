package io.github.junekim0007.cryptobench.preparation

import io.github.junekim0007.cryptobench.preparation.key.plan.KeyCandidate
import io.github.junekim0007.cryptobench.preparation.measurement.Operation
import io.github.junekim0007.cryptobench.preparation.parameter.bind.ParameterBinder
import io.github.junekim0007.cryptobench.preparation.port.Availability
import io.github.junekim0007.cryptobench.preparation.port.DeviceCapability
import io.github.junekim0007.cryptobench.preparation.request.BenchmarkRequest
import io.github.junekim0007.cryptobench.preparation.request.Selection
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

        override fun measuredKey(provider: String, type: String, algorithm: String): KeyCandidate? = KeyCandidate(algorithm.substringBefore('/'))
    }

    private val resolver = CaseResolver(device, ParameterBinder())

    private fun request(vararg selections: Selection) = BenchmarkRequest(selections.toList(), EffectiveFixture.ONE_WARM_RUN)

    @Test
    fun expandsEveryAxisTheTypeIsMeasuredAlong() {
        val request = BenchmarkRequest(
            listOf(Selection("Cipher", "AES/GCM/NoPadding", provider = "AndroidOpenSSL", keySizes = listOf(128, 256))),
            EffectiveFixture.ONE_WARM_RUN.copy(inputSizes = listOf(64, 1024)),
        )
        val resolution = resolver.resolve(request)
        assertEquals(8, resolution.cases.size)
        assertEquals(setOf(Operation.ENCRYPT, Operation.DECRYPT), resolution.cases.map { it.operation }.toSet())
        assertEquals(emptyList<Any>(), resolution.rejections)
    }

    @Test
    fun digestsTakeNoKeyAndKeyGenerationTakesNoInput() {
        val resolution = resolver.resolve(request(
            Selection("MessageDigest", "SHA-256", provider = "AndroidOpenSSL"),
            Selection("MessageDigest", "SHA-256", provider = "BC"),
            Selection("KeyGenerator", "AES", provider = "AndroidOpenSSL", keySizes = listOf(128, 256)),
        ))
        assertEquals(
            listOf(
                "MessageDigest_SHA-256_DIGEST_AndroidOpenSSL_i1024_WARM_fixed",
                "MessageDigest_SHA-256_DIGEST_BC_i1024_WARM_fixed",
                "KeyGenerator_AES_GENERATE-KEY_AndroidOpenSSL_k128_WARM_fixed",
                "KeyGenerator_AES_GENERATE-KEY_AndroidOpenSSL_k256_WARM_fixed",
            ),
            resolution.cases.map { it.id },
        )
    }

    /** The run's input sizes apply only where an entry states none, and only once, here. */
    @Test
    fun theRunInputSizesApplyOnlyWhereAnEntryStatesNone() {
        val resolution = resolver.resolve(BenchmarkRequest(
            listOf(Selection("MessageDigest", "SHA-256", provider = "AndroidOpenSSL"), Selection("MessageDigest", "SHA-256", provider = "BC", inputSizes = listOf(32))),
            EffectiveFixture.ONE_WARM_RUN.copy(inputSizes = listOf(64, 16384)),
        ))
        assertEquals(listOf("AndroidOpenSSL" to 64, "AndroidOpenSSL" to 16384, "BC" to 32), resolution.cases.map { it.provider to it.inputSize })
    }

    /** A setting that reaches no Java call is a mistake in the config, not something to drop quietly. */
    @Test
    fun aSettingNoOperationCanUseIsRejected() {
        assertEquals(listOf("unused_setting"), resolver.resolve(request(Selection("MessageDigest", "SHA-256", provider = "AndroidOpenSSL", keySizes = listOf(256)))).rejections.map { it.reason.substringBefore(':') })
        assertEquals(listOf("unused_setting: [inputSizes] reaches no call of [GENERATE_KEY]"),
            resolver.resolve(request(Selection("KeyGenerator", "AES", provider = "AndroidOpenSSL", inputSizes = listOf(64)))).rejections.map { it.reason })
    }

    /** Every unrunnable request is reported together, so one pass fixes the config. */
    @Test
    fun collectsEveryRejectionWithItsReason() {
        val resolution = resolver.resolve(request(
            Selection("Cipher", "AES/GCM/NoPadding", provider = "AndroidOpenSSL"),
            Selection("Cipher", "AES/GCM/NoPadding", provider = "BC"),
            Selection("Cipher", "AES/GCM/NoPadding", provider = "SunJCE"),
            Selection("Cipher", "ChaCha20", provider = "AndroidOpenSSL"),
        ))
        assertEquals(listOf("AndroidOpenSSL", "AndroidOpenSSL"), resolution.cases.map { it.provider })
        assertEquals(
            listOf(
                "Cipher/AES/GCM/NoPadding@BC: not_registered",
                "Cipher/AES/GCM/NoPadding@SunJCE: provider_not_installed",
                "Cipher/ChaCha20@AndroidOpenSSL: not_registered",
            ),
            resolution.rejections.map { it.toString() },
        )
    }

    /** A parameter that cannot be built rejects its selection; nothing reaches a run. */
    @Test
    fun aBrokenParameterTreeRejectsTheSelection() {
        val broken = Selection("Cipher", "AES/GCM/NoPadding", provider = "AndroidOpenSSL", parameters = mapOf("class" to "javax.crypto.spec.GCMParameterSpec", "arguments" to listOf(128)))
        val bothKeys = Selection("Cipher", "AES/GCM/NoPadding", provider = "AndroidOpenSSL", keySizes = listOf(128),
            keyParameters = mapOf("class" to "java.security.spec.ECGenParameterSpec", "arguments" to listOf("secp256r1")))
        val fine = Selection("Cipher", "AES/GCM/NoPadding", provider = "AndroidOpenSSL", parameters = mapOf("class" to "javax.crypto.spec.GCMParameterSpec", "arguments" to listOf(128, "fresh(12)")))
        val resolution = resolver.resolve(request(broken, bothKeys, fine))
        assertEquals(listOf(fine.parameters, fine.parameters), resolution.cases.map { it.parameters })
        assertEquals(listOf("bind_failed", "key_parameters_and_key_sizes"), resolution.rejections.map { it.reason.substringBefore(':') })
    }

    @Test
    fun aSelectionCanNarrowTheOperations() {
        val verifyOnly = Selection("Cipher", "AES/GCM/NoPadding", provider = "AndroidOpenSSL", operations = setOf(Operation.DECRYPT))
        assertEquals(setOf(Operation.DECRYPT), resolver.resolve(request(verifyOnly)).cases.map { it.operation }.toSet())
    }

    /** Asking a digest to sign is a config mistake: rejected by name, with the operations that type does have. */
    @Test
    fun anOperationTheTypeDoesNotHaveIsRejected() {
        val wrong = Selection("MessageDigest", "SHA-256", provider = "AndroidOpenSSL", operations = setOf(Operation.SIGN))
        assertEquals(listOf("unsupported_operation"), resolver.resolve(request(wrong)).rejections.map { it.reason.substringBefore(':') })
    }
}
