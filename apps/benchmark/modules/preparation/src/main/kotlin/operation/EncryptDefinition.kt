package io.github.junekim0007.cryptobench.preparation.operation

import io.github.junekim0007.cryptobench.preparation.input.CipherKeys
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

    /** One parameter object on two fresh engines: two different nonces mean the provider drew its own. Never the timed engine. */
    override fun parametersIgnored(case: BenchmarkCase, key: KeyMaterial, parameters: BoundParameters?): String? {
        val spec = parameters?.next() ?: return null
        val encrypting = CipherKeys.encrypting(key)
        val (first, second) = List(2) { Cipher.getInstance(case.algorithm, case.provider).apply { init(Cipher.ENCRYPT_MODE, encrypting, spec) }.iv }
        if (first == null || second == null || first.contentEquals(second)) return null
        return "parameters_ignored: ${case.provider} accepted ${spec.javaClass.simpleName} and drew its own nonce; give the form it reads"
    }

    override fun invocation(prepared: PreparedCase): Invocation {
        val key = CipherKeys.encrypting(prepared.key)
        val message = CaseArguments.preparedMessage(prepared)
        val specs = CaseArguments.specPool(prepared.parameters)
        val call = CipherCall({ Cipher.getInstance(prepared.case.algorithm, prepared.case.provider) }, message, { cipher, n ->
            if (specs.isEmpty()) cipher.init(Cipher.ENCRYPT_MODE, key) else cipher.init(Cipher.ENCRYPT_MODE, key, specs[n % specs.size])
        })
        return call.invocation(prepared.case)
    }
}
