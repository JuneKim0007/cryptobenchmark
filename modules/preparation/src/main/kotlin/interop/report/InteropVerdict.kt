package io.github.junekim0007.cryptobench.preparation.interop.report

sealed class Outcome {
    object Pass : Outcome()
    data class Fail(val reason: String) : Outcome()
    data class Untestable(val reason: String) : Outcome()

    val label: String get() = when (this) { Pass -> "pass"; is Fail -> "fail"; is Untestable -> "untested" }
}

data class InteropVerdict(val id: Int, val mode: String, val aToB: Outcome, val bToA: Outcome) {

    val verdict: String get() = when {
        aToB is Outcome.Fail || bToA is Outcome.Fail -> INCOMPATIBLE
        aToB == Outcome.Pass && bToA == Outcome.Pass -> COMPATIBLE
        else -> NOT_TESTABLE
    }

    val reason: String get() = listOf("aToB" to aToB, "bToA" to bToA).mapNotNull { (side, outcome) ->
        when (outcome) {
            is Outcome.Fail -> "$side: ${outcome.reason}"
            is Outcome.Untestable -> "$side: ${outcome.reason}"
            Outcome.Pass -> null
        }
    }.joinToString("; ")

    companion object {
        const val COMPATIBLE = "compatible"
        const val INCOMPATIBLE = "incompatible"
        const val NOT_TESTABLE = "not_testable"
        const val PRODUCE_CONSUME = "produce_consume"
        const val SAME_OUTPUT = "same_output"
        const val NONE = "none"
    }
}
