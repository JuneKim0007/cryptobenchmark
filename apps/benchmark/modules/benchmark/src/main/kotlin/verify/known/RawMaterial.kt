package io.github.junekim0007.cryptobench.benchmark.verify.known

import io.github.junekim0007.cryptobench.preparation.input.OperationInput
import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterial
import io.github.junekim0007.cryptobench.preparation.measurement.Operation
import io.github.junekim0007.cryptobench.preparation.parameter.bind.BoundParameters
import io.github.junekim0007.cryptobench.preparation.parameter.bind.ParameterBinder
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase
import java.security.KeyFactory
import java.security.KeyPair
import java.security.spec.AlgorithmParameterSpec
import java.security.spec.PKCS8EncodedKeySpec
import java.security.spec.X509EncodedKeySpec
import javax.crypto.spec.SecretKeySpec

/** Check mode only: a prepared case with the vector's raw key, fixed parameters and input in place of the generated ones. */
object RawMaterial {

    fun of(vector: KnownAnswer, prepared: PreparedCase): PreparedCase {
        val spec = vector.parameters?.let { spec(it, flip = false) }
        val input = when (prepared.case.operation) {
            Operation.DECRYPT -> OperationInput.Ciphertext(vector.output, vector.input.size, spec, null)
            Operation.VERIFY -> OperationInput.SignedMessage(vector.input, vector.output)
            else -> OperationInput.Message(vector.input)
        }
        // A provider may refuse the same nonce on the next init: the vector's spec alternates with a decoy, and the
        // checked call is an even init of a CipherCall (construction, repeatability probe, then the call).
        val parameters = spec?.let { BoundParameters.cycling(listOf(it, spec(vector.parameters!!, flip = true))) }
        return prepared.copy(key = vector.key?.let { key(it, prepared.case.provider) } ?: prepared.key, parameters = parameters, input = input)
    }

    // The byte arrays a vector's spec fixes (its IV or nonce), to check the call used them.
    fun fixedBytes(tree: Any?): List<ByteArray> = when (tree) {
        is ByteArray -> listOf(tree)
        is Map<*, *> -> tree.values.flatMap { fixedBytes(it) }
        is List<*> -> tree.flatMap { fixedBytes(it) }
        else -> emptyList()
    }

    private fun spec(tree: Map<String, Any>, flip: Boolean): AlgorithmParameterSpec {
        @Suppress("UNCHECKED_CAST")
        val bound = ParameterBinder().bind(numbered(tree, flip) as Map<String, Any>, "knownAnswer.parameters")
        return bound.next()
    }

    private fun numbered(value: Any, flip: Boolean): Any = when (value) {
        is ByteArray -> value.mapIndexed { index, byte -> if (flip && index == value.size - 1) (byte.toInt() xor 1) else byte.toInt() }
        is Map<*, *> -> value.entries.associate { (k, v) -> k.toString() to numbered(v!!, flip) }
        is List<*> -> value.map { numbered(it!!, flip) }
        else -> value
    }

    private fun key(raw: KnownAnswer.RawKey, provider: String): KeyMaterial = when (raw) {
        is KnownAnswer.RawKey.Secret -> KeyMaterial.Secret(SecretKeySpec(raw.bytes, raw.algorithm))
        is KnownAnswer.RawKey.Pair -> {
            val factory = runCatching { KeyFactory.getInstance(raw.algorithm, provider) }.getOrElse { KeyFactory.getInstance(raw.algorithm) }
            KeyMaterial.Pairs(listOf(KeyPair(factory.generatePublic(X509EncodedKeySpec(raw.publicDer)), factory.generatePrivate(PKCS8EncodedKeySpec(raw.privateDer)))))
        }
    }
}
