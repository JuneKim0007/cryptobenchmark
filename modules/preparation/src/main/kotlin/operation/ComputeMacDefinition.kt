package io.github.junekim0007.cryptobench.preparation.operation

import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase
import javax.crypto.Mac

internal object ComputeMacDefinition : OperationDefinition {

    override val keyShape = KeyShape.SECRET
    override val consumesKeySize = true
    override val consumesKeySpec = true
    override val consumesParameters = true
    override val consumesInput = true

    override fun invocation(prepared: PreparedCase): Invocation {
        val mac = Mac.getInstance(prepared.case.algorithm, prepared.case.provider)
        val key = CaseArguments.secret(prepared.key)
        val spec = prepared.parameters?.next()
        if (spec == null) mac.init(key) else mac.init(key, spec)
        val message = CaseArguments.preparedMessage(prepared)
        return Invocation(perIteration = { mac.doFinal(message) })
    }
}
