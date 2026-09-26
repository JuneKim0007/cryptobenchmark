package io.github.junekim0007.cryptobench.preparation.operation

import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase
import javax.crypto.KeyGenerator

internal object GenerateKeyDefinition : OperationDefinition {

    override val keyShape = KeyShape.NONE
    override val consumesKeySize = true
    override val consumesKeySpec = true
    override val consumesParameters = false
    override val consumesInput = false

    override fun invocation(prepared: PreparedCase): Invocation {
        val generator = KeyGenerator.getInstance(prepared.case.algorithm, prepared.case.provider)
        val spec = prepared.keyParameters?.next()
        when {
            spec != null -> generator.init(spec)
            prepared.case.keySize != null -> generator.init(prepared.case.keySize)
        }
        return Invocation(perIteration = { generator.generateKey() })
    }
}
