package io.github.junekim0007.cryptobench.preparation.operation

import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase
import java.security.MessageDigest

internal object DigestDefinition : OperationDefinition {

    override val keyShape = KeyShape.NONE
    override val consumesKeySize = false
    override val consumesKeySpec = false
    override val consumesParameters = false
    override val consumesInput = true

    override fun invocation(prepared: PreparedCase, setup: SetupCatalog): Invocation {
        val message = CaseArguments.preparedMessage(prepared)
        val call = EngineCall({ MessageDigest.getInstance(prepared.case.algorithm, prepared.case.provider) }, { _, _ -> }, { digest -> digest.digest(message) })
        return call.invocation(setup.perCall(prepared.case))
    }
}
