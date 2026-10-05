package io.github.junekim0007.cryptobench.preparation.operation

import io.github.junekim0007.cryptobench.preparation.input.OperationInput
import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterial
import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.parameter.bind.BoundParameters
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase

internal interface OperationDefinition {

    val keyShape: KeyShape

    val consumesKeySize: Boolean

    val consumesInput: Boolean

    val consumesKeySpec: Boolean

    val consumesParameters: Boolean

    fun input(case: BenchmarkCase, key: KeyMaterial, parameters: BoundParameters?): OperationInput =
        if (consumesInput) OperationInput.Message(CaseArguments.seededMessage(case)) else OperationInput.None

    fun invocation(prepared: PreparedCase): Invocation
}
