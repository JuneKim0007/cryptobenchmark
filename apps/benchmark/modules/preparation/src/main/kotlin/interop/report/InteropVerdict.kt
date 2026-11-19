package io.github.junekim0007.cryptobench.preparation.interop.report

import io.github.junekim0007.cryptobench.preparation.interop.plan.InteropPair
import io.github.junekim0007.cryptobench.preparation.peer.Outcome

data class InteropVerdict(val pair: InteropPair, val mode: String, val aToB: Outcome, val bToA: Outcome) {

    val result: String get() = when {
        aToB is Outcome.Fail || bToA is Outcome.Fail -> Outcome.FAIL
        aToB == Outcome.Pass && bToA == Outcome.Pass -> Outcome.PASS
        else -> Outcome.NOT_CHECKABLE
    }

    val reason: String get() = listOf("aToB" to aToB, "bToA" to bToA).mapNotNull { (side, outcome) ->
        when (outcome) {
            is Outcome.Fail -> "$side: ${outcome.reason}"
            is Outcome.NotCheckable -> "$side: ${outcome.reason}"
            Outcome.Pass -> null
        }
    }.joinToString("; ")
}
