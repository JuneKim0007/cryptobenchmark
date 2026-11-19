package io.github.junekim0007.cryptobench.preparation.peer

import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.measurement.Operation
import io.github.junekim0007.cryptobench.preparation.operation.OperationDefinitions

/** The case a peer check's producer runs: seed 0, its key size and input size only where the operation takes them. */
internal object PeerCase {

    // One AES block and below every RSA padding limit: a size every cipher mode in scope accepts.
    const val DEFAULT_INPUT_SIZE = 16

    const val SEED = 0L

    fun of(type: String, algorithm: String, provider: String, operation: Operation, keySize: Int?, inputSize: Int?): BenchmarkCase {
        val definition = OperationDefinitions.of(operation)
        return BenchmarkCase(
            type = type, algorithm = algorithm, provider = provider, operation = operation,
            keySize = if (definition.consumesKeySize) keySize else null,
            inputSize = if (definition.consumesInput) inputSize ?: DEFAULT_INPUT_SIZE else null,
            seed = SEED,
        )
    }
}
