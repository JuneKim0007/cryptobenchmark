package io.github.junekim0007.cryptobench

import androidx.test.platform.app.InstrumentationRegistry

/** The `case` argument: one id, or ids joined by commas in the order to run them; absent keeps every case in plan order. */
object CaseFilter {
    // Paired with scripts/session/case_isolation.py CASE_ARGUMENT.
    const val ARGUMENT = "case"

    fun <T> of(all: List<T>, id: (T) -> String): List<T> {
        val named = InstrumentationRegistry.getArguments().getString(ARGUMENT) ?: return all
        val byId = all.associateBy(id)
        return named.split(',').mapNotNull { byId[it.trim()] }
    }
}
