package io.github.junekim0007.cryptobench.preparation.interop.check

import io.github.junekim0007.cryptobench.preparation.interop.plan.InteropPair
import io.github.junekim0007.cryptobench.preparation.interop.plan.Member
import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.measurement.Operation
import io.github.junekim0007.cryptobench.preparation.operation.OperationDefinitions

internal object PairCases {

    // One AES block and below every RSA padding limit: a size every cipher mode in scope accepts.
    const val DEFAULT_INPUT_SIZE = 16

    const val SEED = 0L

    fun of(member: Member, operation: Operation, pair: InteropPair): BenchmarkCase {
        val definition = OperationDefinitions.of(operation)
        return BenchmarkCase(
            type = member.type, algorithm = member.algorithm, provider = member.provider, operation = operation,
            keySize = if (definition.consumesKeySize) pair.keySize else null,
            inputSize = if (definition.consumesInput) pair.inputSize ?: DEFAULT_INPUT_SIZE else null,
            seed = SEED,
        )
    }
}
