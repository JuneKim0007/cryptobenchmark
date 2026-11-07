package io.github.junekim0007.cryptobench.discovery.contract

import java.security.AlgorithmParameters
import java.security.spec.AlgorithmParameterSpec
import java.security.spec.MGF1ParameterSpec
import java.security.spec.PSSParameterSpec
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.IvParameterSpec
import javax.crypto.spec.OAEPParameterSpec
import javax.crypto.spec.PBEParameterSpec
import javax.crypto.spec.PSource

// One read-back of a spec for every level; a field keeps its prepared.yaml resolvedParameters name. ChaCha20ParameterSpec is absent on Android: reached by name only.
internal object ParameterReadBack {

    const val CLASS = "class"

    val CHACHA: Class<*>? = Attempt.of { Class.forName("javax.crypto.spec.ChaCha20ParameterSpec") }.getOrNull()

    private val READABLE: List<Class<out AlgorithmParameterSpec>> =
        listOf(GCMParameterSpec::class.java, OAEPParameterSpec::class.java, PBEParameterSpec::class.java, IvParameterSpec::class.java, PSSParameterSpec::class.java)

    fun readable(parameters: AlgorithmParameters): AlgorithmParameterSpec? =
        READABLE.firstNotNullOfOrNull { type -> Attempt.of { parameters.getParameterSpec(type) }.getOrNull() }
            ?: CHACHA?.let { type -> Attempt.of { parameters.getParameterSpec(type.asSubclass(AlgorithmParameterSpec::class.java)) }.getOrNull() }

    fun describe(spec: AlgorithmParameterSpec): Map<String, Any> {
        val fields = linkedMapOf<String, Any>(CLASS to spec.javaClass.simpleName)
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
            spec is PSSParameterSpec -> {
                fields["digest"] = spec.digestAlgorithm
                (spec.mgfParameters as? MGF1ParameterSpec)?.let { fields["mgf1"] = it.digestAlgorithm }
                fields["saltBytes"] = spec.saltLength
            }
            isChaCha(spec) -> { fields["ivBytes"] = chaChaNonce(spec).size; fields["counter"] = chaChaCounter(spec) }
        }
        return fields
    }

    fun isChaCha(spec: AlgorithmParameterSpec): Boolean = CHACHA?.isInstance(spec) == true

    fun chaChaNonce(spec: AlgorithmParameterSpec): ByteArray = call(spec, "getNonce") as ByteArray

    fun chaChaCounter(spec: AlgorithmParameterSpec): Int = call(spec, "getCounter") as Int

    private fun call(target: Any, method: String): Any = target.javaClass.getMethod(method).invoke(target)
}
