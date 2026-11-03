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
        val key = CaseArguments.secret(prepared.key)
        val spec = prepared.parameters?.next()
        val message = CaseArguments.preparedMessage(prepared)
        val call = EngineCall({ Mac.getInstance(prepared.case.algorithm, prepared.case.provider) },
            { mac, _ -> if (spec == null) mac.init(key) else mac.init(key, spec) }, { mac -> mac.doFinal(message) })
        return call.invocation(SetupCatalog.standard.perCall(prepared.case))
    }
}
