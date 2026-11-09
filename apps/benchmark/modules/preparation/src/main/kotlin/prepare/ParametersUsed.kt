package io.github.junekim0007.cryptobench.preparation.prepare

import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterial
import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.measurement.Operation
import io.github.junekim0007.cryptobench.preparation.parameter.bind.BoundParameters
import java.security.spec.AlgorithmParameterSpec
import javax.crypto.Cipher

/** A provider can accept a parameter object and not use it: encrypt then runs on a nonce of its own. A separate engine, never the timed one. */
internal object ParametersUsed {

    private val READERS = listOf("getIV", "getNonce")

    fun problem(case: BenchmarkCase, material: KeyMaterial, parameters: BoundParameters?): String? {
        val key = material.secretKeyOrNull
        if (case.type != "Cipher" || case.operation != Operation.ENCRYPT || parameters == null || key == null) return null
        val spec = parameters.next()
        val supplied = supplied(spec) ?: return null
        val used = Cipher.getInstance(case.algorithm, case.provider).also { it.init(Cipher.ENCRYPT_MODE, key, spec) }.iv ?: return null
        return if (used.contentEquals(supplied)) null else "parameters_ignored: ${case.provider} accepted ${spec.javaClass.simpleName} and used a nonce of its own; give the form it reads"
    }

    private fun supplied(spec: AlgorithmParameterSpec): ByteArray? =
        spec.javaClass.methods.firstOrNull { it.name in READERS && it.parameterCount == 0 }?.invoke(spec) as? ByteArray
}
