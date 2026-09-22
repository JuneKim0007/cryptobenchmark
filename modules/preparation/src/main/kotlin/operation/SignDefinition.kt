package io.github.junekim0007.cryptobench.preparation.operation

import io.github.junekim0007.cryptobench.preparation.engine.CaseEngines
import io.github.junekim0007.cryptobench.preparation.input.OperationInput
import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterial
import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.parameter.bind.BoundParameters
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase

internal object SignDefinition : OperationDefinition {

    override val keyShape = KeyShape.PAIR
    override val consumesKeySize = true
    override val consumesInput = true

    override fun input(case: BenchmarkCase, key: KeyMaterial, parameters: BoundParameters?): OperationInput =
        OperationInput.Message(CaseArguments.seededMessage(case))

    override fun check(prepared: PreparedCase) {
        val signature = CaseEngines.signature(prepared.case)
        prepared.parameters?.next()?.let { signature.setParameter(it) }
        signature.initSign(CaseArguments.pair(prepared.key).private)
        signature.update(CaseArguments.preparedMessage(prepared))
        signature.sign()
    }
}
