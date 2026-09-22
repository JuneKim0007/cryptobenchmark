package io.github.junekim0007.cryptobench.preparation.operation

import io.github.junekim0007.cryptobench.preparation.engine.CaseEngines
import io.github.junekim0007.cryptobench.preparation.input.OperationInput
import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterial
import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.parameter.bind.BoundParameters
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase

internal object VerifyDefinition : OperationDefinition {

    override val keyShape = KeyShape.PAIR
    override val consumesKeySize = true
    override val consumesKeySpec = true
    override val consumesParameters = true
    override val consumesInput = true

    override fun input(case: BenchmarkCase, key: KeyMaterial, parameters: BoundParameters?): OperationInput {
        val message = CaseArguments.seededMessage(case)
        val pair = key.keyPairsOrNull?.first() ?: throw IllegalArgumentException("verify_needs_a_key_pair: ${case.id}")
        val spec = parameters?.next()
        val signing = CaseEngines.signature(case)
        if (spec != null) signing.setParameter(spec)
        signing.initSign(pair.private)
        signing.update(message)
        val signature = signing.sign()
        val verifying = CaseEngines.signature(case)
        if (spec != null) verifying.setParameter(spec)
        verifying.initVerify(pair.public)
        verifying.update(message)
        check(verifying.verify(signature)) { "round_trip_failed: the signature does not verify" }
        return OperationInput.SignedMessage(message, signature)
    }

    override fun check(prepared: PreparedCase) {
        val input = prepared.input as? OperationInput.SignedMessage ?: throw IllegalArgumentException("verify_without_signature")
        val signature = CaseEngines.signature(prepared.case)
        prepared.parameters?.next()?.let { signature.setParameter(it) }
        signature.initVerify(CaseArguments.pair(prepared.key).public)
        signature.update(input.message)
        check(signature.verify(input.signature)) { "verify_failed" }
    }
}
