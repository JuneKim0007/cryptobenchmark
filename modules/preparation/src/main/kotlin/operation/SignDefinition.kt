package io.github.junekim0007.cryptobench.preparation.operation

import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase
import java.security.Signature

internal object SignDefinition : OperationDefinition {

    override val keyShape = KeyShape.PAIR
    override val consumesKeySize = true
    override val consumesKeySpec = true
    override val consumesParameters = true
    override val consumesInput = true

    override fun invocation(prepared: PreparedCase): Invocation {
        val signature = Signature.getInstance(prepared.case.algorithm, prepared.case.provider)
        prepared.parameters?.next()?.let { signature.setParameter(it) }
        signature.initSign(CaseArguments.pair(prepared.key).private)
        val message = CaseArguments.preparedMessage(prepared)
        return Invocation(perIteration = {
            signature.update(message)
            signature.sign()
        })
    }
}
