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
import javax.crypto.MacSpi
import javax.crypto.spec.IvParameterSpec
import org.junit.Test
import java.security.InvalidAlgorithmParameterException
import java.security.Key
import java.security.Provider
import java.security.PrivateKey
import java.security.PublicKey
import java.security.Security
import java.security.SignatureSpi
import java.security.spec.AlgorithmParameterSpec

// A GMAC as BC's: no doFinal after doFinal without init, and a nonce once per key.
class OneShotGmac : MacSpi() {
    private val seen = HashSet<List<Byte>>()
    private var ready = false
    override fun engineGetMacLength() = 16
    override fun engineInit(key: Key?, params: AlgorithmParameterSpec?) {
        val iv = (params as? IvParameterSpec)?.iv?.toList() ?: throw InvalidAlgorithmParameterException("iv required")
        if (!seen.add(iv)) throw InvalidAlgorithmParameterException("nonce reused")
        ready = true
    }
    override fun engineUpdate(input: Byte) = Unit
    override fun engineUpdate(input: ByteArray?, offset: Int, len: Int) = Unit
    override fun engineDoFinal(): ByteArray {
        check(ready) { "doFinal without init" }
        ready = false
        return ByteArray(16)
    }
    override fun engineReset() = Unit
}

/**
 * One invocation is built once and called many times: the dry run calls it once to prove the case
 * runs, the harness times the same lambda. Anything a second call would break has to surface here,
 * not in a measurement.
 */
// A signature that is its parameter: it verifies only under the spec it was signed under.
class SpecBoundSignature : SignatureSpi() {
    private var spec = ByteArray(0)
    override fun engineSetParameter(params: AlgorithmParameterSpec?) { spec = (params as IvParameterSpec).iv }
    override fun engineInitVerify(key: PublicKey?) = Unit
    override fun engineInitSign(key: PrivateKey?) = Unit
    override fun engineUpdate(b: Byte) = Unit
    override fun engineUpdate(b: ByteArray?, off: Int, len: Int) = Unit
    override fun engineSign(): ByteArray = spec.copyOf()
    override fun engineVerify(sig: ByteArray?): Boolean = sig.contentEquals(spec)
    @Deprecated("the JCA abstract member") override fun engineSetParameter(param: String?, value: Any?) = Unit
    @Deprecated("the JCA abstract member") override fun engineGetParameter(param: String?): Any? = null
}

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

    @Test
    fun gmacFixedReinitsWithAFreshNonceEveryCall() {
        @Suppress("DEPRECATION")
        val provider = object : Provider("OneShotGmac", 1.0, "GMAC that resets to nothing") {
            init { put("Mac.TEST-GMAC", OneShotGmac::class.java.name) }
        }
        Security.addProvider(provider)
        try {
            val iv = ParameterBinder().bind(mapOf("class" to "javax.crypto.spec.IvParameterSpec", "arguments" to listOf("fresh(12)")), "parameters")
            val invocation = Invocations.of(prepared("Mac", "TEST-GMAC", provider.name, Operation.COMPUTE_MAC, key = aes, parameters = iv))
            assertEquals(PerCall.INIT_AND_OPERATION, invocation.perCall)
            repeat(4) { invocation.perIteration() }
        } finally {
            Security.removeProvider(provider.name)
        }
    }

    @Test
    fun verifyTimesTheSpecItsSignatureWasMadeUnder() {
        @Suppress("DEPRECATION")
        val provider = object : Provider("SpecBound", 1.0, "a signature under one spec") {
            init { put("Signature.SPEC-BOUND", SpecBoundSignature::class.java.name) }
        }
        Security.addProvider(provider)
        try {
            val drawn = ParameterBinder().bind(mapOf("class" to "javax.crypto.spec.IvParameterSpec", "arguments" to listOf("fresh(16)")), "parameters")
            val invocation = Invocations.of(prepared("Signature", "SPEC-BOUND", provider.name, Operation.VERIFY, key = ec, parameters = drawn))
            repeat(3) { invocation.perIteration() }
        } finally {
            Security.removeProvider(provider.name)
        }
    }
}
