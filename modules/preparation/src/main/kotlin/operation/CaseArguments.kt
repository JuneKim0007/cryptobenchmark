package io.github.junekim0007.cryptobench.preparation.operation

import io.github.junekim0007.cryptobench.preparation.input.InputBytes
import io.github.junekim0007.cryptobench.preparation.input.OperationInput
import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterial
import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase

internal object CaseArguments {

    fun seededMessage(case: BenchmarkCase): ByteArray = InputBytes.of(case.seed, case.inputSize ?: 0)

    fun preparedMessage(prepared: PreparedCase): ByteArray =
        (prepared.input as? OperationInput.Message)?.bytes ?: ByteArray(prepared.case.inputSize ?: 0)

    fun secret(key: KeyMaterial) =
        key.secretKeyOrNull ?: throw IllegalArgumentException("mac_needs_a_secret_key")

    fun pair(key: KeyMaterial) =
        key.keyPairsOrNull?.first() ?: throw IllegalArgumentException("signature_needs_a_key_pair")
}
