package io.github.junekim0007.cryptobench.benchmark

import io.github.junekim0007.cryptobench.preparation.input.InputBytes
import io.github.junekim0007.cryptobench.preparation.input.OperationInput
import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterial
import io.github.junekim0007.cryptobench.preparation.key.plan.KeyCandidate
import io.github.junekim0007.cryptobench.preparation.key.plan.KeyRecipe
import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.measurement.Operation
import io.github.junekim0007.cryptobench.preparation.measurement.Variant
import io.github.junekim0007.cryptobench.preparation.operation.Invocations
import io.github.junekim0007.cryptobench.preparation.parameter.bind.ParameterBinder
import io.github.junekim0007.cryptobench.preparation.parameter.resolve.ResolvedParameters
import io.github.junekim0007.cryptobench.preparation.port.Availability
import io.github.junekim0007.cryptobench.preparation.port.DeviceCapability
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase
import java.io.File
import javax.crypto.KeyGenerator

/** Prepared cases on the JDK's own providers, as preparation leaves them, for the end-to-end check's tests. */
object CheckFixture {

    val knownAnswers = File("src/test/resources/known-answers-fixture.yaml")

    fun digest(variant: Variant = Variant.FIXED, size: Int = 64) = prepared(PreparedCase(
        BenchmarkCase("MessageDigest", "SHA-256", "SUN", Operation.DIGEST, inputSize = size, variant = variant),
        KeyRecipe.None, KeyMaterial.None, null, null, OperationInput.Message(InputBytes.of(0, size)),
    ))

    fun gcmEncrypt(variant: Variant = Variant.FIXED, keySize: Int = 128): PreparedCase {
        val key = KeyGenerator.getInstance("AES", "SunJCE").apply { init(keySize) }.generateKey()
        val parameters = ParameterBinder().bind(mapOf("class" to "javax.crypto.spec.GCMParameterSpec", "arguments" to listOf(128, "fresh(12)")), "parameters")
        return prepared(PreparedCase(
            BenchmarkCase("Cipher", "AES/GCM/NoPadding", "SunJCE", Operation.ENCRYPT, keySize = keySize, inputSize = 64, variant = variant),
            KeyRecipe.Secret("AES", keySize, "SunJCE"), KeyMaterial.Secret(key), parameters, null, OperationInput.Message(InputBytes.of(0, 64)),
            mapOf(ResolvedParameters.IV_BYTES to 12, ResolvedParameters.TAG_BITS to 128),
        ))
    }

    fun mac() = prepared(PreparedCase(
        BenchmarkCase("Mac", "HmacSHA256", "SunJCE", Operation.COMPUTE_MAC, keySize = 256, inputSize = 64),
        KeyRecipe.Secret("HmacSHA256", 256, "SunJCE"), KeyMaterial.Secret(KeyGenerator.getInstance("HmacSHA256", "SunJCE").generateKey()), null, null, OperationInput.Message(InputBytes.of(0, 64)),
    ))

    // perCall as preparation records it: from the invocation it built.
    private fun prepared(case: PreparedCase) = case.copy(perCall = Invocations.of(case).perCall)

    // Only the case's own provider: no peer for the cross-provider oracle.
    val alone = object : DeviceCapability {
        override fun providers() = listOf("SUN", "SunJCE")
        override fun check(provider: String, type: String, algorithm: String): Availability = Availability.Unavailable("not_in_fixture")
        override fun measuredKey(provider: String, type: String, algorithm: String): KeyCandidate? = null
    }

    // PeerProvider beside the JDK's: a peer for SHA-256 and HmacSHA256.
    val withPeer = object : DeviceCapability {
        override fun providers() = listOf("SUN", "SunJCE", PeerProvider.NAME)
        override fun check(provider: String, type: String, algorithm: String): Availability =
            if (provider == PeerProvider.NAME) Availability.Available else Availability.Unavailable("not_in_fixture")
        override fun measuredKey(provider: String, type: String, algorithm: String): KeyCandidate? = null
    }
}
