package io.github.junekim0007.cryptobench.preparation.operation

import io.github.junekim0007.cryptobench.preparation.input.CipherKeys
import io.github.junekim0007.cryptobench.preparation.input.OperationInput
import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterial
import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.parameter.bind.BoundParameters
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase
import javax.crypto.Cipher

internal object DecryptDefinition : OperationDefinition {

    override val keyShape = KeyShape.DEVICE_DECIDES
    override val consumesKeySize = true
    override val consumesKeySpec = true
    override val consumesParameters = true
    override val consumesInput = true

    override fun input(case: BenchmarkCase, key: KeyMaterial, parameters: BoundParameters?): OperationInput {
        val plaintext = CaseArguments.seededMessage(case)
        val spec = parameters?.next()
        val encrypting = Cipher.getInstance(case.algorithm, case.provider)
        if (spec == null) encrypting.init(Cipher.ENCRYPT_MODE, CipherKeys.encrypting(key)) else encrypting.init(Cipher.ENCRYPT_MODE, CipherKeys.encrypting(key), spec)
        val input = OperationInput.Ciphertext(encrypting.doFinal(plaintext), plaintext.size, spec, if (spec == null) encrypting.parameters else null)
        val decrypting = Cipher.getInstance(case.algorithm, case.provider)
        input.initDecrypting(decrypting, CipherKeys.decrypting(key))
        check(decrypting.doFinal(input.bytes).contentEquals(plaintext)) { "round_trip_failed: decrypt does not return the plaintext" }
        return input
    }

    override fun invocation(prepared: PreparedCase): Invocation {
        val input = prepared.input as? OperationInput.Ciphertext ?: throw IllegalArgumentException("decrypt_without_ciphertext")
        val cipher = Cipher.getInstance(prepared.case.algorithm, prepared.case.provider)
        val key = CipherKeys.decrypting(prepared.key)
        return Invocation(perIteration = {
            input.initDecrypting(cipher, key)
            cipher.doFinal(input.bytes)
        })
    }
}
