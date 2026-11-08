package io.github.junekim0007.cryptobench

import io.github.junekim0007.cryptobench.benchmark.run.CaseSettings
import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.operation.Invocations
import org.junit.Test
import org.junit.runner.RunWith
import org.junit.runners.Parameterized

// The listing names each case without preparing it; the test prepares only its own, so a provider that throws loses this case alone.
@RunWith(Parameterized::class)
class CryptoBenchmark(caseId: String, private val case: BenchmarkCase) : JetpackCase(caseId, CaseSettings.of(case)) {

    @Test
    fun measure() = timed {
        val prepared = DevicePlan.prepared(case) ?: error("not_prepared: ${DevicePlan.skipOf(case)}")
        Invocations.of(prepared).perIteration
    }

    companion object {

        @JvmStatic
        @Parameterized.Parameters(name = "{0}")
        fun cases(): List<Array<Any>> = DevicePlan.timedCases.map { case -> arrayOf(case.id, case) }
    }
}
