package io.github.junekim0007.cryptobench.preparation.operation

import io.github.junekim0007.cryptobench.preparation.input.OperationInput
import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterial
import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.parameter.bind.BoundParameters
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase
import javax.crypto.KeyAgreement

internal object AgreeKeyDefinition : OperationDefinition {

    override val keyShape = KeyShape.PEER_PAIRS
    override val consumesKeySize = true
    override val consumesKeySpec = true
    override val consumesParameters = true
    override val consumesInput = false

    override fun input(case: BenchmarkCase, key: KeyMaterial, parameters: BoundParameters?): OperationInput = OperationInput.None

    override fun check(prepared: PreparedCase) {
        val pairs = prepared.key.keyPairsOrNull ?: throw IllegalArgumentException("agreement_needs_key_pairs")
        val agreement = KeyAgreement.getInstance(prepared.case.algorithm, prepared.case.provider)
        val spec = prepared.parameters?.next()
        if (spec == null) agreement.init(pairs.first().private) else agreement.init(pairs.first().private, spec)
        agreement.doPhase(pairs.last().public, true)
        agreement.generateSecret()
    }
}
