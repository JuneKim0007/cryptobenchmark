package io.github.junekim0007.cryptobench.preparation

import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterial
import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterialGenerator
import io.github.junekim0007.cryptobench.preparation.key.plan.KeyRecipe
import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.measurement.Operation
import io.github.junekim0007.cryptobench.preparation.measurement.Variant
import io.github.junekim0007.cryptobench.preparation.operation.PerCall
import io.github.junekim0007.cryptobench.preparation.operation.Invocations
import io.github.junekim0007.cryptobench.preparation.operation.OperationDefinitions
import io.github.junekim0007.cryptobench.preparation.parameter.bind.BoundParameters
import io.github.junekim0007.cryptobench.preparation.parameter.bind.ParameterBinder
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertSame
import javax.crypto.Cipher
import org.junit.Test

/**
 * One invocation is built once and called many times: the dry run calls it once to prove the case
 * runs, the harness times the same lambda. Anything a second call would break has to surface here,
 * not in a measurement.
 */
class InvocationTest {

    private val keys = KeyMaterialGenerator()
    private val aes = keys.generate(KeyRecipe.Secret("AES", 128, "SunJCE"))
    private val ec = keys.generate(KeyRecipe.Pair("EC", 256, "SunEC"))

    private fun gcm(): BoundParameters =
        ParameterBinder().bind(mapOf("class" to "javax.crypto.spec.GCMParameterSpec", "arguments" to listOf(128, "fresh(12)")), "parameters")

    private fun prepared(
        type: String,
        algorithm: String,
        provider: String,
        operation: Operation,
        key: KeyMaterial = KeyMaterial.None,
        parameters: BoundParameters? = null,
        keySize: Int? = null,
        inputSize: Int? = 64,
        variant: Variant = Variant.FIXED,
    ): PreparedCase {
        val case = BenchmarkCase(type, algorithm, provider, operation, keySize = keySize, inputSize = inputSize, seed = 7, variant = variant)
        val input = OperationDefinitions.of(operation).input(case, key, parameters)
        return PreparedCase(case, KeyRecipe.None, key, parameters, null, input)
    }

    private val everyShape = listOf(
        prepared("MessageDigest", "SHA-256", "SUN", Operation.DIGEST),
        prepared("Mac", "HmacSHA256", "SunJCE", Operation.COMPUTE_MAC, key = aes),
        prepared("Cipher", "AES/GCM/NoPadding", "SunJCE", Operation.ENCRYPT, key = aes, parameters = gcm()),
        prepared("Cipher", "AES/CBC/PKCS5Padding", "SunJCE", Operation.DECRYPT, key = aes),
        prepared("Signature", "SHA256withECDSA", "SunEC", Operation.SIGN, key = ec),
        prepared("Signature", "SHA256withECDSA", "SunEC", Operation.VERIFY, key = ec),
        prepared("KeyGenerator", "AES", "SunJCE", Operation.GENERATE_KEY, keySize = 128, inputSize = null),
        prepared("KeyPairGenerator", "EC", "SunEC", Operation.GENERATE_KEY_PAIR, keySize = 256, inputSize = null),
    )

    @Test
    fun anInvocationProvedByOneCallSurvivesTheIterationsAHarnessWillRun() {
        everyShape.forEach { prepared ->
            val invocation = Invocations.of(prepared)
            assertNotNull(prepared.case.id, invocation.once())
            repeat(3) { assertNotNull(prepared.case.id, invocation.perIteration()) }
        }
    }

    @Test
    fun bothVariantsOfEveryShapeSurviveTheIterations() {
        everyShape.map { it.copy(case = it.case.copy(variant = Variant.NOT_FIXED)) }.forEach { prepared ->
            val invocation = Invocations.of(prepared)
            assertNotNull(prepared.case.id, invocation.once())
            repeat(3) { assertNotNull(prepared.case.id, invocation.perIteration()) }
        }
    }

    @Test
    fun gcmFixedStillInitsWithAFreshIvOnOneInstance() {
        val invocation = Invocations.of(prepared("Cipher", "AES/GCM/NoPadding", "SunJCE", Operation.ENCRYPT, key = aes, parameters = gcm()))
        assertEquals(PerCall.INIT_AND_OPERATION, invocation.perCall)
        val engine = invocation.engine as Cipher
        val ivs = (1..4).map { invocation.perIteration(); assertSame(engine, invocation.engine); engine.iv.toList() }
        assertEquals(ivs.size, ivs.toSet().size)
    }

    @Test
    fun notFixedMakesANewInstanceEveryCallAndFixedKeepsOne() {
        val sign = prepared("Signature", "SHA256withECDSA", "SunEC", Operation.SIGN, key = ec)
        val fixed = Invocations.of(sign)
        val kept = fixed.engine
        repeat(2) { fixed.perIteration(); assertSame(kept, fixed.engine) }
        val notFixed = Invocations.of(sign.copy(case = sign.case.copy(variant = Variant.NOT_FIXED)))
        assertEquals(PerCall.INSTANCE_INIT_AND_OPERATION, notFixed.perCall)
        val engines = (1..3).map { notFixed.perIteration(); notFixed.engine }
        assertEquals(3, engines.toSet().size)
    }
}
