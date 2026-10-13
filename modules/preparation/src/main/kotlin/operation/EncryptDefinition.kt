package io.github.junekim0007.cryptobench.preparation.operation

import io.github.junekim0007.cryptobench.preparation.input.CipherKeys
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase
import javax.crypto.Cipher

internal object EncryptDefinition : OperationDefinition {

    override val keyShape = KeyShape.DEVICE_DECIDES
    override val consumesKeySize = true
    override val consumesKeySpec = true
    override val consumesParameters = true
    override val consumesInput = true

    override fun invocation(prepared: PreparedCase): Invocation {
        val cipher = Cipher.getInstance(prepared.case.algorithm, prepared.case.provider)
        val key = CipherKeys.encrypting(prepared.key)
        val message = CaseArguments.preparedMessage(prepared)
        val specs = CaseArguments.specPool(prepared.parameters)
        val call = CipherCall(cipher, message, { n ->
            if (specs.isEmpty()) cipher.init(Cipher.ENCRYPT_MODE, key) else cipher.init(Cipher.ENCRYPT_MODE, key, specs[n % specs.size])
        }, perCallParameters = specs.size > 1)
        return call.invocation()
    }
}
