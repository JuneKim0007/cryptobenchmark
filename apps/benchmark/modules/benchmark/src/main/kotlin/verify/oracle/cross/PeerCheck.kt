package io.github.junekim0007.cryptobench.benchmark.verify.oracle.cross

import io.github.junekim0007.cryptobench.benchmark.verify.oracle.CheckedCall
import io.github.junekim0007.cryptobench.preparation.interop.report.Outcome
import io.github.junekim0007.cryptobench.preparation.shared.FailureText
import java.security.GeneralSecurityException
import java.security.InvalidAlgorithmParameterException
import java.security.InvalidKeyException
import java.security.NoSuchAlgorithmException
import javax.crypto.NoSuchPaddingException

/** One peer provider's check of the case's own output, from the case's key, parameters and input. */
internal fun interface PeerCheck {
    fun against(call: CheckedCall, peer: String): Outcome
}

/** What the peer cannot take is not_checkable with a code; the peer refusing or contradicting the case's output fails it. */
internal class PeerRefusal(val code: String, detail: String) : Exception(detail)

internal object PeerRun {

    fun <S> of(setup: () -> S, judge: (S) -> Outcome): Outcome {
        val ready = try {
            setup()
        } catch (refused: PeerRefusal) {
            return Outcome.NotCheckable("${refused.code}: ${refused.message}")
        } catch (refused: InvalidKeyException) {
            return Outcome.NotCheckable("peer_key_rejected: ${FailureText.of(refused)}")
        } catch (refused: InvalidAlgorithmParameterException) {
            return Outcome.NotCheckable("peer_parameters_rejected: ${FailureText.of(refused)}")
        } catch (missing: NoSuchAlgorithmException) {
            return Outcome.NotCheckable("peer_unavailable: ${FailureText.of(missing)}")
        } catch (missing: NoSuchPaddingException) {
            return Outcome.NotCheckable("peer_unavailable: ${FailureText.of(missing)}")
        } catch (failure: Exception) {
            return Outcome.NotCheckable("peer_setup_failed: ${FailureText.of(failure)}")
        }
        return try {
            judge(ready)
        } catch (refused: GeneralSecurityException) {
            Outcome.Fail("peer_refused: ${FailureText.of(refused)}")
        } catch (failure: Exception) {
            Outcome.NotCheckable("peer_error: ${FailureText.of(failure)}")
        }
    }

    fun agrees(same: Boolean, failure: String): Outcome = if (same) Outcome.Pass else Outcome.Fail(failure)
}
