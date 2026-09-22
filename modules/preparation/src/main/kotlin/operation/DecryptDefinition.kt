package io.github.junekim0007.cryptobench.preparation.operation

import io.github.junekim0007.cryptobench.preparation.engine.CaseEngines
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
        val encrypting = CaseEngines.cipher(case)
        if (spec == null) encrypting.init(Cipher.ENCRYPT_MODE, CipherKeys.encrypting(key)) else encrypting.init(Cipher.ENCRYPT_MODE, CipherKeys.encrypting(key), spec)
        val input = OperationInput.Ciphertext(encrypting.doFinal(plaintext), plaintext.size, spec, if (spec == null) encrypting.parameters else null)
        val decrypting = CaseEngines.cipher(case)
        input.initDecrypting(decrypting, CipherKeys.decrypting(key))
        check(decrypting.doFinal(input.bytes).contentEquals(plaintext)) { "round_trip_failed: decrypt does not return the plaintext" }
        return input
    }

    override fun check(prepared: PreparedCase) {
        val input = prepared.input as? OperationInput.Ciphertext ?: throw IllegalArgumentException("decrypt_without_ciphertext")
        val cipher = CaseEngines.cipher(prepared.case)
        input.initDecrypting(cipher, CipherKeys.decrypting(prepared.key))
        check(cipher.doFinal(input.bytes).size == input.plaintextSize) { "decrypt_size_mismatch" }
    }
}
