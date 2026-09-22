package io.github.junekim0007.cryptobench.preparation.operation

import io.github.junekim0007.cryptobench.preparation.input.OperationInput
import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterial
import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.parameter.bind.BoundParameters
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase
import javax.crypto.KeyGenerator

internal object GenerateKeyDefinition : OperationDefinition {

    override val keyShape = KeyShape.NONE
    override val consumesKeySize = true
    override val consumesKeySpec = true
    override val consumesParameters = false
    override val consumesInput = false

    override fun input(case: BenchmarkCase, key: KeyMaterial, parameters: BoundParameters?): OperationInput = OperationInput.None

    override fun check(prepared: PreparedCase) {
        val generator = KeyGenerator.getInstance(prepared.case.algorithm, prepared.case.provider)
        val spec = prepared.keyParameters?.next()
        when {
            spec != null -> generator.init(spec)
            prepared.case.keySize != null -> generator.init(prepared.case.keySize)
        }
        generator.generateKey()
    }
}
