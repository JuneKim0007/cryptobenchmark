package io.github.junekim0007.cryptobench.benchmark.verify.oracle.contract

import io.github.junekim0007.cryptobench.preparation.interop.report.Outcome
import io.github.junekim0007.cryptobench.preparation.parameter.resolve.ResolvedParameters
import java.security.GeneralSecurityException

/** Authenticated (the provider read back a tag length): a changed ciphertext must be refused; otherwise not asserted. */
internal object Tamper {

    fun refused(resolved: Map<String, Any>, decrypt: () -> ByteArray): Outcome {
        if (ResolvedParameters.TAG_BITS !in resolved) return Outcome.NotCheckable("not_authenticated: no tag length read back")
        return try {
            decrypt()
            Outcome.Fail("tamper_accepted: a changed ciphertext decrypted")
        } catch (refused: GeneralSecurityException) {
            Outcome.Pass
        }
    }
}
