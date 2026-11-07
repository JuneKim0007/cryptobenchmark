package io.github.junekim0007.cryptobench.benchmark.verify.oracle.contract

import io.github.junekim0007.cryptobench.benchmark.verify.oracle.CheckedCall
import io.github.junekim0007.cryptobench.preparation.input.CipherKeys
import io.github.junekim0007.cryptobench.preparation.input.OperationInput
import io.github.junekim0007.cryptobench.preparation.interop.report.Outcome
import javax.crypto.Cipher

/** Encrypt: the output fits the engine's own size bound, the same provider's decrypt under its reported parameters recovers the input, a tag refuses tampering. */
internal object EncryptProperties : Properties {

    override fun of(call: CheckedCall): Map<String, Outcome> {
        val cipher = call.invocation.engine as? Cipher ?: return mapOf("engine" to Outcome.NotCheckable("no_engine_read_back"))
        val input = (call.prepared.input as? OperationInput.Message)?.bytes ?: return mapOf("input" to Outcome.NotCheckable("no_message_input"))
        val output = call.output as? ByteArray ?: return mapOf("output" to Outcome.Fail("not_bytes: ${call.output?.javaClass?.simpleName}"))
        val bound = runCatching { cipher.getOutputSize(input.size) }.getOrNull()?.takeIf { it >= 0 }
        val reported = cipher.parameters
        val decrypt = { bytes: ByteArray ->
            val reverse = Cipher.getInstance(call.prepared.case.algorithm, call.prepared.case.provider)
            val key = CipherKeys.decrypting(call.prepared.key)
            if (reported != null) reverse.init(Cipher.DECRYPT_MODE, key, reported) else reverse.init(Cipher.DECRYPT_MODE, key)
            reverse.doFinal(bytes)
        }
        val reverse = if (reported == null && cipher.iv != null) Outcome.NotCheckable("parameters_not_reported: the engine has an IV but no AlgorithmParameters")
        else runCatching { decrypt(output) }.let { back ->
            holds(back.getOrNull()?.contentEquals(input) == true) {
                back.exceptionOrNull()?.let { "reverse_failed: ${it.javaClass.simpleName}: ${it.message}" } ?: "reverse_differs: decrypt did not return the input"
            }
        }
        return linkedMapOf(
            "length" to if (bound == null) Outcome.NotCheckable("no_size_bound: getOutputSize refused or -1 after the call")
            else holds(output.size in input.size..bound) { "length: ${output.size} bytes for ${input.size} in, the engine bounds it at $bound" },
            "reverse" to reverse,
            "tamper" to if (reverse is Outcome.NotCheckable) reverse else Tamper.refused(call.prepared.resolvedParameters) { decrypt(flipped(output)) },
        )
    }
}
