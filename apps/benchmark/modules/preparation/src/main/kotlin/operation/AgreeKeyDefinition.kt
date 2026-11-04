package io.github.junekim0007.cryptobench.preparation.operation

import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase
import javax.crypto.KeyAgreement

internal object AgreeKeyDefinition : OperationDefinition {

    override val keyShape = KeyShape.PEER_PAIRS
    override val consumesKeySize = true
    override val consumesKeySpec = true
    override val consumesParameters = true
    override val consumesInput = false

    override fun invocation(prepared: PreparedCase): Invocation {
        val pairs = prepared.key.keyPairsOrNull ?: throw IllegalArgumentException("agreement_needs_key_pairs")
        val spec = prepared.parameters?.next()
        val call = EngineCall({ KeyAgreement.getInstance(prepared.case.algorithm, prepared.case.provider) },
            { agreement, _ -> if (spec == null) agreement.init(pairs.first().private) else agreement.init(pairs.first().private, spec) },
            { agreement ->
                agreement.doPhase(pairs.last().public, true)
                agreement.generateSecret()
            })
        return call.invocation(SetupCatalog.standard.perCall(prepared.case))
    }
}
