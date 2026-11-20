package io.github.junekim0007.cryptobench.preparation.peer

sealed class Outcome {
    // Outcome.Pass is the plain pass; a pass by a generated key's use names it
    open class Pass internal constructor(val detail: String?) : Outcome() {
        companion object : Pass(null)
    }
    data class Fail(val reason: String) : Outcome()
    data class NotCheckable(val reason: String) : Outcome()

    val label: String get() = when (this) {
        is Pass -> PASS
        is Fail -> FAIL
        is NotCheckable -> NOT_CHECKABLE
    }

    companion object {
        const val PASS = "pass"
        const val FAIL = "fail"
        const val NOT_CHECKABLE = "not_checkable"
    }
}
