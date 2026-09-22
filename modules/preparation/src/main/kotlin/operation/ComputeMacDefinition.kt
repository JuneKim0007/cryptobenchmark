package io.github.junekim0007.cryptobench.preparation.operation

import io.github.junekim0007.cryptobench.preparation.input.OperationInput
import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterial
import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.parameter.bind.BoundParameters
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase
import javax.crypto.Mac

internal object ComputeMacDefinition : OperationDefinition {

    override val keyShape = KeyShape.SECRET
    override val consumesKeySize = true
    override val consumesInput = true

    override fun input(case: BenchmarkCase, key: KeyMaterial, parameters: BoundParameters?): OperationInput =
        OperationInput.Message(CaseArguments.seededMessage(case))

    override fun check(prepared: PreparedCase) {
        Mac.getInstance(prepared.case.algorithm, prepared.case.provider)
            .apply { init(CaseArguments.secret(prepared.key)) }
            .doFinal(CaseArguments.preparedMessage(prepared))
    }
}
