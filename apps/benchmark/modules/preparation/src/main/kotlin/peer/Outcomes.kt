package io.github.junekim0007.cryptobench.preparation.peer

import io.github.junekim0007.cryptobench.document.catalogue.Recipes
import io.github.junekim0007.cryptobench.jca.bind.BindException
import io.github.junekim0007.cryptobench.preparation.shared.FailureText
import java.security.GeneralSecurityException
import java.security.InvalidAlgorithmParameterException
import java.security.InvalidKeyException
import java.security.NoSuchAlgorithmException
import java.security.NoSuchProviderException
import java.security.spec.InvalidKeySpecException
import javax.crypto.NoSuchPaddingException

// OUTPUT_KEY_SETUP: the consumer's setup over a key the produced call generated, which it must take; USE_PARAMETERS: that key's use's parameters
enum class Stage { PRODUCE, SETUP, OUTPUT_KEY_SETUP, CONSUME, USE_PARAMETERS }

/** A peer check's failure to its verdict: the first rule for the failing stage that matches the exception. */
object Outcomes {

    private class Rule(val stages: Set<Stage>, val code: String?, val fail: Boolean, val matches: (Throwable) -> Boolean)

    private val SETUPS = setOf(Stage.SETUP, Stage.OUTPUT_KEY_SETUP)
    private const val KEY_REJECTED = "peer_key_rejected"

    private fun missing(failure: Throwable) = failure is NoSuchAlgorithmException || failure is NoSuchPaddingException || failure is NoSuchProviderException

    private fun keyRefused(failure: Throwable) = failure is InvalidKeyException || failure is InvalidKeySpecException

    // code null: a PeerRefusal's or a coded exception's own code
    private val RULES = listOf(
        Rule(setOf(Stage.USE_PARAMETERS), null, false) { it is Recipes.Unbuildable || it is BindException },
        Rule(setOf(Stage.USE_PARAMETERS), "use_parameters_failed", false) { true },
        Rule(setOf(Stage.PRODUCE), "producer_failed", false) { true },
        Rule(setOf(Stage.OUTPUT_KEY_SETUP), KEY_REJECTED, true) { (it is PeerRefusal && it.code == KEY_REJECTED) || keyRefused(it) },
        Rule(SETUPS + Stage.CONSUME, null, false) { it is PeerRefusal },
        Rule(SETUPS, "peer_unavailable", false, ::missing),
        Rule(SETUPS, KEY_REJECTED, false, ::keyRefused),
        Rule(SETUPS, "peer_parameters_rejected", false) { it is InvalidAlgorithmParameterException },
        Rule(SETUPS, "peer_setup_failed", false) { true },
        Rule(setOf(Stage.CONSUME), "peer_unavailable", false, ::missing),
        Rule(setOf(Stage.CONSUME), "peer_refused", true) { it is GeneralSecurityException },
        Rule(setOf(Stage.CONSUME), "peer_error", false) { true },
    )

    fun of(stage: Stage, failure: Throwable): Outcome {
        val rule = RULES.first { stage in it.stages && it.matches(failure) }
        val reason = when {
            failure is PeerRefusal && (rule.code == null || rule.code == failure.code) -> "${failure.code}: ${failure.message}"
            rule.code == null -> FailureText.stable(failure.message.orEmpty())
            else -> "${rule.code}: ${FailureText.of(failure)}"
        }
        return if (rule.fail) Outcome.Fail(reason) else Outcome.NotCheckable(reason)
    }
}
