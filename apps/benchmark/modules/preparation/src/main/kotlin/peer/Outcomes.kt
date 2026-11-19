package io.github.junekim0007.cryptobench.preparation.peer

import io.github.junekim0007.cryptobench.preparation.shared.FailureText
import java.security.GeneralSecurityException
import java.security.InvalidAlgorithmParameterException
import java.security.InvalidKeyException
import java.security.NoSuchAlgorithmException
import javax.crypto.NoSuchPaddingException

enum class Stage { SETUP, CONSUME }

/** A peer check's failure to its verdict: the first rule of the failing stage that matches the exception. */
object Outcomes {

    private class Rule(val stage: Stage, val code: String?, val fail: Boolean, val matches: (Throwable) -> Boolean)

    // code null: a PeerRefusal's own code
    private val RULES = listOf(
        Rule(Stage.SETUP, null, false) { it is PeerRefusal },
        Rule(Stage.SETUP, "peer_key_rejected", false) { it is InvalidKeyException },
        Rule(Stage.SETUP, "peer_parameters_rejected", false) { it is InvalidAlgorithmParameterException },
        Rule(Stage.SETUP, "peer_unavailable", false) { it is NoSuchAlgorithmException || it is NoSuchPaddingException },
        Rule(Stage.SETUP, "peer_setup_failed", false) { true },
        Rule(Stage.CONSUME, "peer_refused", true) { it is GeneralSecurityException },
        Rule(Stage.CONSUME, "peer_error", false) { true },
    )

    fun of(stage: Stage, failure: Throwable): Outcome {
        val rule = RULES.first { it.stage == stage && it.matches(failure) }
        val reason = rule.code?.let { "$it: ${FailureText.of(failure)}" } ?: "${(failure as PeerRefusal).code}: ${failure.message}"
        return if (rule.fail) Outcome.Fail(reason) else Outcome.NotCheckable(reason)
    }
}
