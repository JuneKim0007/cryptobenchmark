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
        val spec = prepared.parameters?.next()
        val private = CaseArguments.pair(prepared.key).private
        val message = CaseArguments.preparedMessage(prepared)
        val call = EngineCall({ Signature.getInstance(prepared.case.algorithm, prepared.case.provider) }, { signature, _ ->
            spec?.let { signature.setParameter(it) }
            signature.initSign(private)
        }, { signature ->
            signature.update(message)
            signature.sign()
        })
        return call.invocation(SetupCatalog.standard.perCall(prepared.case), readBack = true)
    }
}
