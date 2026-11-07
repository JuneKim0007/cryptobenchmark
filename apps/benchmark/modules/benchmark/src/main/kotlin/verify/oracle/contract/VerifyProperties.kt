package io.github.junekim0007.cryptobench.benchmark.verify.oracle.contract

import io.github.junekim0007.cryptobench.benchmark.verify.oracle.CheckedCall
import io.github.junekim0007.cryptobench.preparation.input.OperationInput
import io.github.junekim0007.cryptobench.preparation.interop.report.Outcome
import java.security.GeneralSecurityException
import java.security.Signature

/** Verify: the call returned, so verify was true inside it; the same provider refuses a changed signature. */
internal object VerifyProperties : Properties {

    override fun of(call: CheckedCall): Map<String, Outcome> {
        val input = call.prepared.input as? OperationInput.SignedMessage ?: return mapOf("input" to Outcome.NotCheckable("no_signed_input"))
        val spec = call.prepared.parameters?.next()
        val tampered = runCatching {
            val verifier = Signature.getInstance(call.prepared.case.algorithm, call.prepared.case.provider)
            spec?.let { verifier.setParameter(it) }
            verifier.initVerify(call.prepared.key.keyPairsOrNull!!.first().public)
            verifier.update(input.message)
            try { verifier.verify(flipped(input.signature, input.signature.size / 2)) } catch (refused: GeneralSecurityException) { false }
        }.getOrDefault(false)
        return linkedMapOf("verify" to Outcome.Pass, "tamper" to holds(!tampered) { "tamper_accepted: a changed signature verifies" })
    }
}
