package io.github.junekim0007.cryptobench

import org.junit.Test
import org.junit.runner.RunWith
import org.junit.runners.Parameterized

// The host names the cases with `-e case`: ScopedInterop decided which scopes are measured.
@RunWith(Parameterized::class)
class ScopedBenchmark(caseId: String, private val prepare: () -> () -> Any?) : JetpackCase(caseId, ScopedPlan.settings) {

    @Test
    fun measure() = timed(prepare)

    companion object {

        @JvmStatic
        @Parameterized.Parameters(name = "{0}")
        fun cases(): List<Array<Any>> = CaseFilter.of(ScopedPlan.variants()) { it[0] as String }
    }
}
