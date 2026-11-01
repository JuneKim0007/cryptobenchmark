package io.github.junekim0007.cryptobench.preparation.parameter.resolve

import java.security.AlgorithmParameters
import java.security.spec.AlgorithmParameterSpec
import java.security.spec.InvalidParameterSpecException
import java.security.spec.MGF1ParameterSpec
import java.security.spec.PSSParameterSpec
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.IvParameterSpec
import javax.crypto.spec.OAEPParameterSpec
import javax.crypto.spec.PSource

/** Fields of the parameters an engine reports, read by spec class. ivCandidate is an IvParameterSpec length, not yet known to be an IV. */
internal class SpecFields(val fields: Map<String, Any>, val ivCandidate: Int?) {

    companion object {

        private val READ_ORDER = listOf(GCMParameterSpec::class.java, OAEPParameterSpec::class.java, PSSParameterSpec::class.java, IvParameterSpec::class.java)

        fun of(parameters: AlgorithmParameters?): SpecFields {
            if (parameters == null) return SpecFields(emptyMap(), null)
            for (type in READ_ORDER) {
                val spec = specOrNull(parameters, type) ?: continue
                return of(spec)
            }
            return SpecFields(emptyMap(), null)
        }

        fun of(spec: AlgorithmParameterSpec): SpecFields = when (spec) {
            is GCMParameterSpec -> SpecFields(linkedMapOf(ResolvedParameters.IV_BYTES to spec.iv.size, ResolvedParameters.TAG_BITS to spec.tLen), null)
            is OAEPParameterSpec -> SpecFields(LinkedHashMap<String, Any>().apply {
                put(ResolvedParameters.DIGEST, spec.digestAlgorithm)
                (spec.mgfParameters as? MGF1ParameterSpec)?.let { put(ResolvedParameters.MGF1, it.digestAlgorithm) }
                (spec.pSource as? PSource.PSpecified)?.let { put(ResolvedParameters.LABEL_BYTES, it.value.size) }
            }, null)
            is PSSParameterSpec -> SpecFields(LinkedHashMap<String, Any>().apply {
                put(ResolvedParameters.DIGEST, spec.digestAlgorithm)
                (spec.mgfParameters as? MGF1ParameterSpec)?.let { put(ResolvedParameters.MGF1, it.digestAlgorithm) }
            }, null)
            is IvParameterSpec -> SpecFields(emptyMap(), spec.iv.size)
            else -> SpecFields(emptyMap(), null)
        }

        private fun <T : AlgorithmParameterSpec> specOrNull(parameters: AlgorithmParameters, type: Class<T>): T? = try {
            parameters.getParameterSpec(type)
        } catch (notThisType: InvalidParameterSpecException) {
            null
        }
    }
}
