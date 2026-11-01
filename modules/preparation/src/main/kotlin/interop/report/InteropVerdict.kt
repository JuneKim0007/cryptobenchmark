package io.github.junekim0007.cryptobench.preparation.interop.report

import io.github.junekim0007.cryptobench.preparation.interop.plan.InteropPair

sealed class Outcome {
    object Pass : Outcome()
    data class Fail(val reason: String) : Outcome()
    data class NotCheckable(val reason: String) : Outcome()

    val label: String get() = when (this) {
        Pass -> InteropVerdict.PASS
        is Fail -> InteropVerdict.FAIL
        is NotCheckable -> InteropVerdict.NOT_CHECKABLE
    }
}

data class InteropVerdict(val pair: InteropPair, val mode: String, val aToB: Outcome, val bToA: Outcome) {

    val result: String get() = when {
        aToB is Outcome.Fail || bToA is Outcome.Fail -> FAIL
        aToB == Outcome.Pass && bToA == Outcome.Pass -> PASS
        else -> NOT_CHECKABLE
    }

    val reason: String get() = listOf("aToB" to aToB, "bToA" to bToA).mapNotNull { (side, outcome) ->
        when (outcome) {
            is Outcome.Fail -> "$side: ${outcome.reason}"
            is Outcome.NotCheckable -> "$side: ${outcome.reason}"
            Outcome.Pass -> null
        }
    }.joinToString("; ")

    companion object {
        const val PASS = "pass"
        const val FAIL = "fail"
        const val NOT_CHECKABLE = "not_checkable"
        const val PRODUCE_CONSUME = "produce_consume"
        const val SAME_OUTPUT = "same_output"
        const val NONE = "none"
    }
}
