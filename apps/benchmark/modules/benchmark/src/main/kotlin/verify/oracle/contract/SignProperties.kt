package io.github.junekim0007.cryptobench.benchmark.verify.oracle.contract

import io.github.junekim0007.cryptobench.benchmark.verify.oracle.CheckedCall
import io.github.junekim0007.cryptobench.preparation.input.OperationInput
import io.github.junekim0007.cryptobench.preparation.interop.report.Outcome
import java.security.GeneralSecurityException
import java.security.Signature

/** Sign: the same provider verifies the signature with the public key, and refuses it over a changed message. */
internal object SignProperties : Properties {

    override fun of(call: CheckedCall): Map<String, Outcome> {
        val message = (call.prepared.input as? OperationInput.Message)?.bytes ?: return mapOf("input" to Outcome.NotCheckable("no_message_input"))
        val signature = call.output as? ByteArray ?: return mapOf("output" to Outcome.Fail("not_bytes: ${call.output?.javaClass?.simpleName}"))
        val spec = call.prepared.parameters?.next()
        val verifies = { bytes: ByteArray ->
            val verifier = Signature.getInstance(call.prepared.case.algorithm, call.prepared.case.provider)
            spec?.let { verifier.setParameter(it) }
            verifier.initVerify(call.prepared.key.keyPairsOrNull!!.first().public)
            verifier.update(bytes)
            try { verifier.verify(signature) } catch (refused: GeneralSecurityException) { false }
        }
        return linkedMapOf(
            "verify" to holds(runCatching { verifies(message) }.getOrDefault(false)) { "verify_false: the provider refuses its own signature" },
            "tamper" to holds(!runCatching { verifies(flipped(message, 0)) }.getOrDefault(false)) { "tamper_accepted: the signature verifies over a changed message" },
        )
    }
}
