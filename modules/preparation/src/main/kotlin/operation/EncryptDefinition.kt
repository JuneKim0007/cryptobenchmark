package io.github.junekim0007.cryptobench.preparation.operation

import io.github.junekim0007.cryptobench.preparation.engine.CaseEngines
import io.github.junekim0007.cryptobench.preparation.input.CipherKeys
import io.github.junekim0007.cryptobench.preparation.input.OperationInput
import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterial
import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.parameter.bind.BoundParameters
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase
import javax.crypto.Cipher

internal object EncryptDefinition : OperationDefinition {

    override val keyShape = KeyShape.DEVICE_DECIDES
    override val consumesKeySize = true
    override val consumesKeySpec = true
    override val consumesParameters = true
    override val consumesInput = true

    override fun input(case: BenchmarkCase, key: KeyMaterial, parameters: BoundParameters?): OperationInput =
        OperationInput.Message(CaseArguments.seededMessage(case))

    override fun check(prepared: PreparedCase) {
        val cipher = CaseEngines.cipher(prepared.case)
        val key = CipherKeys.encrypting(prepared.key)
        val spec = prepared.parameters?.next()
        if (spec == null) cipher.init(Cipher.ENCRYPT_MODE, key) else cipher.init(Cipher.ENCRYPT_MODE, key, spec)
        cipher.doFinal(CaseArguments.preparedMessage(prepared))
    }
}
