package io.github.junekim0007.cryptobench.preparation.operation

import io.github.junekim0007.cryptobench.preparation.input.InputBytes
import io.github.junekim0007.cryptobench.preparation.input.OperationInput
import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterial
import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.parameter.bind.BoundParameters
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase
import java.security.spec.AlgorithmParameterSpec

internal object CaseArguments {

    private const val SPEC_POOL_SIZE = 256

    fun specPool(parameters: BoundParameters?): List<AlgorithmParameterSpec> = when {
        parameters == null -> emptyList()
        parameters.varies -> (1..SPEC_POOL_SIZE).map { parameters.next() }
        else -> listOf(parameters.next())
    }

    fun seededMessage(case: BenchmarkCase): ByteArray = InputBytes.of(case.seed, case.inputSize ?: 0)

    fun preparedMessage(prepared: PreparedCase): ByteArray =
        (prepared.input as? OperationInput.Message)?.bytes ?: ByteArray(prepared.case.inputSize ?: 0)

    fun secret(key: KeyMaterial) =
        key.secretKeyOrNull ?: throw IllegalArgumentException("mac_needs_a_secret_key")

    fun pair(key: KeyMaterial) =
        key.keyPairsOrNull?.first() ?: throw IllegalArgumentException("signature_needs_a_key_pair")
}
