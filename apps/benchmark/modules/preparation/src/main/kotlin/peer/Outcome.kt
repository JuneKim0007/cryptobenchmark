package io.github.junekim0007.cryptobench.preparation.peer

sealed class Outcome {
    object Pass : Outcome()
    data class Fail(val reason: String) : Outcome()
    data class NotCheckable(val reason: String) : Outcome()

    val label: String get() = when (this) {
        Pass -> PASS
        is Fail -> FAIL
        is NotCheckable -> NOT_CHECKABLE
    }

    companion object {
        const val PASS = "pass"
        const val FAIL = "fail"
        const val NOT_CHECKABLE = "not_checkable"
    }
}
