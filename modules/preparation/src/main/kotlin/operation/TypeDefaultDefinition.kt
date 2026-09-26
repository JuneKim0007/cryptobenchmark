package io.github.junekim0007.cryptobench.preparation.operation

import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase

internal object TypeDefaultDefinition : OperationDefinition {

    override val keyShape = KeyShape.DEVICE_DECIDES
    override val consumesKeySize = true
    override val consumesKeySpec = true
    override val consumesParameters = true
    override val consumesInput = true

    override fun invocation(prepared: PreparedCase): Invocation = Invocation(perIteration = { null })
}
