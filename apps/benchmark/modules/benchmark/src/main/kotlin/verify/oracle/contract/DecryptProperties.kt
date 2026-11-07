package io.github.junekim0007.cryptobench.benchmark.verify.oracle.contract

import io.github.junekim0007.cryptobench.benchmark.verify.oracle.CheckedCall
import io.github.junekim0007.cryptobench.preparation.input.CipherKeys
import io.github.junekim0007.cryptobench.preparation.input.InputBytes
import io.github.junekim0007.cryptobench.preparation.input.OperationInput
import io.github.junekim0007.cryptobench.preparation.interop.report.Outcome
import javax.crypto.Cipher

/** Decrypt: the output is the seeded plaintext the ciphertext was made from; a tag refuses a changed ciphertext. */
internal object DecryptProperties : Properties {

    override fun of(call: CheckedCall): Map<String, Outcome> {
        val input = call.prepared.input as? OperationInput.Ciphertext ?: return mapOf("input" to Outcome.NotCheckable("no_ciphertext_input"))
        val output = call.output as? ByteArray ?: return mapOf("output" to Outcome.Fail("not_bytes: ${call.output?.javaClass?.simpleName}"))
        val plaintext = InputBytes.of(call.prepared.case.seed, input.plaintextSize)
        val tampered = {
            val cipher = Cipher.getInstance(call.prepared.case.algorithm, call.prepared.case.provider)
            input.initDecrypting(cipher, CipherKeys.decrypting(call.prepared.key))
            cipher.doFinal(flipped(input.bytes))
        }
        return linkedMapOf(
            "reverse" to holds(output.contentEquals(plaintext)) { "reverse_differs: ${output.size} bytes, the plaintext has ${plaintext.size}" },
            "tamper" to Tamper.refused(call.prepared.resolvedParameters, tampered),
        )
    }
}
