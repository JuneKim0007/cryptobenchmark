package io.github.junekim0007.cryptobench.preparation.input

import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterial
import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.measurement.Operation
import io.github.junekim0007.cryptobench.preparation.parameter.bind.BoundParameters
import java.security.Signature
import javax.crypto.Cipher

class InputPreparer {

    fun prepare(case: BenchmarkCase, key: KeyMaterial, parameters: BoundParameters?): OperationInput = when (case.operation) {
        Operation.ENCRYPT, Operation.SIGN, Operation.DIGEST, Operation.COMPUTE_MAC, Operation.TYPE_DEFAULT -> OperationInput.Message(message(case))
        Operation.DECRYPT -> ciphertext(case, key, parameters)
        Operation.VERIFY -> signedMessage(case, key, parameters)
        Operation.GENERATE_KEY, Operation.GENERATE_KEY_PAIR, Operation.AGREE_KEY -> OperationInput.None
    }

    private fun message(case: BenchmarkCase): ByteArray = InputBytes.of(case.seed, case.inputSize ?: 0)

    private fun ciphertext(case: BenchmarkCase, key: KeyMaterial, parameters: BoundParameters?): OperationInput.Ciphertext {
        val plaintext = message(case)
        val spec = parameters?.next()
        val encrypting = Cipher.getInstance(case.algorithm, case.provider)
        if (spec == null) encrypting.init(Cipher.ENCRYPT_MODE, CipherKeys.encrypting(key)) else encrypting.init(Cipher.ENCRYPT_MODE, CipherKeys.encrypting(key), spec)
        val input = OperationInput.Ciphertext(encrypting.doFinal(plaintext), plaintext.size, spec, if (spec == null) encrypting.parameters else null)
        val decrypting = Cipher.getInstance(case.algorithm, case.provider)
        when {
            input.spec != null -> decrypting.init(Cipher.DECRYPT_MODE, CipherKeys.decrypting(key), input.spec)
            input.providerParameters != null -> decrypting.init(Cipher.DECRYPT_MODE, CipherKeys.decrypting(key), input.providerParameters)
            else -> decrypting.init(Cipher.DECRYPT_MODE, CipherKeys.decrypting(key))
        }
        check(decrypting.doFinal(input.bytes).contentEquals(plaintext)) { "round_trip_failed: decrypt does not return the plaintext" }
        return input
    }

    private fun signedMessage(case: BenchmarkCase, key: KeyMaterial, parameters: BoundParameters?): OperationInput.SignedMessage {
        val message = message(case)
        val pair = (key as? KeyMaterial.Pairs)?.pairs?.first() ?: throw IllegalArgumentException("verify_needs_a_key_pair: ${case.id}")
        val spec = parameters?.next()
        val signing = Signature.getInstance(case.algorithm, case.provider)
        if (spec != null) signing.setParameter(spec)
        signing.initSign(pair.private)
        signing.update(message)
        val signature = signing.sign()
        val verifying = Signature.getInstance(case.algorithm, case.provider)
        if (spec != null) verifying.setParameter(spec)
        verifying.initVerify(pair.public)
        verifying.update(message)
        check(verifying.verify(signature)) { "round_trip_failed: the signature does not verify" }
        return OperationInput.SignedMessage(message, signature)
    }
}
