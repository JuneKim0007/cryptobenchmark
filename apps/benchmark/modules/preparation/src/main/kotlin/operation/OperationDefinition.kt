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

    val consumesArtifact: Boolean get() = false

    fun input(case: BenchmarkCase, key: KeyMaterial, parameters: BoundParameters?): OperationInput =
        if (consumesInput) OperationInput.Message(CaseArguments.seededMessage(case)) else OperationInput.None

    /** Why a provider accepted this case's parameters and did not use them; null when it used them or nothing can tell. */
    fun parametersIgnored(case: BenchmarkCase, key: KeyMaterial, parameters: BoundParameters?): String? = null

    fun invocation(prepared: PreparedCase): Invocation
}
