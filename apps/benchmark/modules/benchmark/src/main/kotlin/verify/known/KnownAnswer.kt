package io.github.junekim0007.cryptobench.benchmark.verify.known

import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.measurement.Operation

/** One sourced vector: raw key, fixed parameters, input and expected output; a case matches by type, any of its spellings, operation and key bits. */
class KnownAnswer(
    val id: String,
    val source: String,
    val type: String,
    val algorithms: List<String>,
    val operations: Set<Operation>,
    val key: RawKey?,
    val parameters: Map<String, Any>?,
    val input: ByteArray,
    val output: ByteArray,
    val prefixOnly: Boolean,
) {

    sealed class RawKey {
        abstract val algorithm: String
        class Secret(override val algorithm: String, val bytes: ByteArray) : RawKey()
        class Pair(override val algorithm: String, val privateDer: ByteArray, val publicDer: ByteArray) : RawKey()
    }

    fun matches(case: BenchmarkCase): Boolean =
        type.equals(case.type, ignoreCase = true) && algorithms.any { it.equals(case.algorithm, ignoreCase = true) } && case.operation in operations &&
            (case.keySize == null || key !is RawKey.Secret || key.bytes.size * Byte.SIZE_BITS == case.keySize)
}
