package io.github.junekim0007.cryptobench.preparation.operation

import io.github.junekim0007.cryptobench.preparation.input.OperationInput
import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterial
import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.parameter.bind.BoundParameters
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase
import java.security.MessageDigest

internal object DigestDefinition : OperationDefinition {

    override val keyShape = KeyShape.NONE
    override val consumesKeySize = false
    override val consumesKeySpec = false
    override val consumesParameters = false
    override val consumesInput = true

    override fun input(case: BenchmarkCase, key: KeyMaterial, parameters: BoundParameters?): OperationInput =
        OperationInput.Message(CaseArguments.seededMessage(case))

    override fun check(prepared: PreparedCase) {
        MessageDigest.getInstance(prepared.case.algorithm, prepared.case.provider).digest(CaseArguments.preparedMessage(prepared))
    }
}
