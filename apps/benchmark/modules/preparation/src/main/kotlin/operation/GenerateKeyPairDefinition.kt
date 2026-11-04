package io.github.junekim0007.cryptobench.preparation.operation

import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase
import java.security.KeyPairGenerator

internal object GenerateKeyPairDefinition : OperationDefinition {

    override val keyShape = KeyShape.NONE
    override val consumesKeySize = true
    override val consumesKeySpec = true
    override val consumesParameters = false
    override val consumesInput = false

    override fun invocation(prepared: PreparedCase): Invocation {
        val generator = KeyPairGenerator.getInstance(prepared.case.algorithm, prepared.case.provider)
        val spec = prepared.keyParameters?.next()
        when {
            spec != null -> generator.initialize(spec)
            prepared.case.keySize != null -> generator.initialize(prepared.case.keySize)
        }
        return Invocation(perIteration = { generator.generateKeyPair() })
    }
}
