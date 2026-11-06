package io.github.junekim0007.cryptobench.discovery.trial.requirement

import java.security.AlgorithmParameters
import java.security.SecureRandom
import java.security.spec.AlgorithmParameterSpec
import java.security.spec.MGF1ParameterSpec
import java.security.spec.PSSParameterSpec
import javax.crypto.Cipher
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.IvParameterSpec
import javax.crypto.spec.OAEPParameterSpec
import javax.crypto.spec.PBEParameterSpec
import javax.crypto.spec.PSource

// Every variation is built from a spec a provider accepted, so no algorithm is named here. ChaCha20ParameterSpec is absent on Android: reached by name only.
internal object ParameterSpecs {

    private val RANDOM = SecureRandom()

    private val CHACHA: Class<*>? = runCatching { Class.forName("javax.crypto.spec.ChaCha20ParameterSpec") }.getOrNull()

    private val READABLE: List<Class<out AlgorithmParameterSpec>> =
        listOf(GCMParameterSpec::class.java, OAEPParameterSpec::class.java, PBEParameterSpec::class.java, IvParameterSpec::class.java, PSSParameterSpec::class.java)

    fun candidates(): List<Pair<String, AlgorithmParameterSpec>> = listOfNotNull(
        "IvParameterSpec(16)" to IvParameterSpec(random(16)),
        "IvParameterSpec(12)" to IvParameterSpec(random(12)),
        "IvParameterSpec(8)" to IvParameterSpec(random(8)),
        "GCMParameterSpec(128,12)" to GCMParameterSpec(128, random(12)),
        chaCha(random(12), 1)?.let { "ChaCha20ParameterSpec(12,1)" to it },
        "OAEPParameterSpec.DEFAULT" to OAEPParameterSpec.DEFAULT,
        "PBEParameterSpec(16,1000,iv16)" to PBEParameterSpec(random(16), 1000, IvParameterSpec(random(16))),
        "PBEParameterSpec(16,1000)" to PBEParameterSpec(random(16), 1000),
        "PBEParameterSpec(8,1000)" to PBEParameterSpec(random(8), 1000),
        "PSSParameterSpec.DEFAULT" to PSSParameterSpec.DEFAULT,
    )

    fun generated(cipher: Cipher): AlgorithmParameterSpec? =
        cipher.parameters?.let { readable(it) } ?: cipher.iv?.let { IvParameterSpec(it) }

    fun readable(parameters: AlgorithmParameters): AlgorithmParameterSpec? =
        READABLE.firstNotNullOfOrNull { type -> runCatching { parameters.getParameterSpec(type) }.getOrNull() }
            ?: CHACHA?.let { type -> runCatching { parameters.getParameterSpec(type.asSubclass(AlgorithmParameterSpec::class.java)) }.getOrNull() }

    fun ivOf(spec: AlgorithmParameterSpec?): ByteArray? = when {
        spec is GCMParameterSpec -> spec.iv
        spec is IvParameterSpec -> spec.iv
        spec is PBEParameterSpec -> (spec.parameterSpec as? IvParameterSpec)?.iv
        spec != null && isChaCha(spec) -> call(spec, "getNonce") as ByteArray
        else -> null
    }

    fun withIv(spec: AlgorithmParameterSpec, iv: ByteArray): AlgorithmParameterSpec = when {
        spec is GCMParameterSpec -> GCMParameterSpec(spec.tLen, iv)
        spec is PBEParameterSpec -> PBEParameterSpec(spec.salt, spec.iterationCount, IvParameterSpec(iv))
        isChaCha(spec) -> chaCha(iv, call(spec, "getCounter") as Int)!!
        else -> IvParameterSpec(iv)
    }

    // A new IV of the same length, so a reuse guard never answers for another fact.
    fun fresh(spec: AlgorithmParameterSpec?): AlgorithmParameterSpec? {
        val iv = ivOf(spec) ?: return spec
        return withIv(spec!!, random(iv.size))
    }

    fun oaep(digest: String, mgf1: String, label: ByteArray): OAEPParameterSpec =
        OAEPParameterSpec(digest, OAEPParameterSpec.DEFAULT.mgfAlgorithm, MGF1ParameterSpec(mgf1), PSource.PSpecified(label))

    fun describe(spec: AlgorithmParameterSpec): Map<String, Any> {
        val fields = linkedMapOf<String, Any>("class" to spec.javaClass.simpleName)
        when {
            spec is GCMParameterSpec -> { fields["ivBytes"] = spec.iv.size; fields["tagBits"] = spec.tLen }
            spec is IvParameterSpec -> fields["ivBytes"] = spec.iv.size
            spec is OAEPParameterSpec -> {
                fields["digest"] = spec.digestAlgorithm
                (spec.mgfParameters as? MGF1ParameterSpec)?.let { fields["mgf1"] = it.digestAlgorithm }
                (spec.pSource as? PSource.PSpecified)?.let { fields["labelBytes"] = it.value.size }
            }
            spec is PBEParameterSpec -> {
                fields["saltBytes"] = spec.salt.size
                fields["iterations"] = spec.iterationCount
                (spec.parameterSpec as? IvParameterSpec)?.let { fields["innerIvBytes"] = it.iv.size }
            }
            spec is PSSParameterSpec -> { fields["digest"] = spec.digestAlgorithm; fields["saltBytes"] = spec.saltLength }
            isChaCha(spec) -> { fields["ivBytes"] = (call(spec, "getNonce") as ByteArray).size; fields["counter"] = call(spec, "getCounter") }
        }
        return fields
    }

    fun random(length: Int): ByteArray = ByteArray(length).also { RANDOM.nextBytes(it) }

    private fun isChaCha(spec: AlgorithmParameterSpec): Boolean = CHACHA?.isInstance(spec) == true

    private fun chaCha(nonce: ByteArray, counter: Int): AlgorithmParameterSpec? =
        CHACHA?.getConstructor(ByteArray::class.java, Int::class.javaPrimitiveType)?.newInstance(nonce, counter) as AlgorithmParameterSpec?

    private fun call(target: Any, method: String): Any = target.javaClass.getMethod(method).invoke(target)
}
