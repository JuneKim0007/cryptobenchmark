package io.github.junekim0007.cryptobench

import androidx.test.platform.app.InstrumentationRegistry

/** The `case` argument: one id, or ids joined by commas in the order to run them; absent keeps every case in plan order. */
object CaseFilter {
    // Paired with apps/benchmark-runner/session/case_isolation.py CASE_ARGUMENT.
    const val ARGUMENT = "case"

    private val argument: String? get() = InstrumentationRegistry.getArguments().getString(ARGUMENT)

    val named: Boolean get() = argument != null

    fun <T> of(all: List<T>, id: (T) -> String): List<T> {
        val named = argument ?: return all
        val byId = all.associateBy(id)
        return named.split(',').mapNotNull { byId[it.trim()] }
    }
}
