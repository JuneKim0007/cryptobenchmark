package io.github.junekim0007.cryptobench.preparation.operation

import io.github.junekim0007.cryptobench.preparation.input.OperationInput
import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterial
import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.parameter.bind.BoundParameters
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase
import java.security.KeyPairGenerator

internal object GenerateKeyPairDefinition : OperationDefinition {

    override val keyShape = KeyShape.NONE
    override val consumesKeySize = true
    override val consumesInput = false

    override fun input(case: BenchmarkCase, key: KeyMaterial, parameters: BoundParameters?): OperationInput = OperationInput.None

    override fun check(prepared: PreparedCase) {
        KeyPairGenerator.getInstance(prepared.case.algorithm, prepared.case.provider)
            .also { generator -> prepared.case.keySize?.let { generator.initialize(it) } }
            .generateKeyPair()
    }
}
