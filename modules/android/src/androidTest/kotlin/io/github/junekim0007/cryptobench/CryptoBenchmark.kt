package io.github.junekim0007.cryptobench

import androidx.benchmark.BlackHole
import androidx.benchmark.ExperimentalBenchmarkConfigApi
import androidx.benchmark.junit4.BenchmarkRule
import androidx.benchmark.junit4.measureRepeated
import io.github.junekim0007.cryptobench.benchmark.run.compose.CaseRuns
import io.github.junekim0007.cryptobench.benchmark.run.CaseSettings
import io.github.junekim0007.cryptobench.preparation.operation.Invocations
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.junit.runners.Parameterized

@OptIn(ExperimentalBenchmarkConfigApi::class)
@RunWith(Parameterized::class)
class CryptoBenchmark(private val caseId: String, private val prepared: PreparedCase) {

    private val settings = CaseSettings.of(prepared.case.harness)

    @get:Rule
    val benchmarkRule = BenchmarkRule(JetpackConfig.of(settings))

    @Test
    fun measure() {
        val invocation = Invocations.of(prepared)
        CaseRuns.timed(caseId, settings.energy) {
            benchmarkRule.measureRepeated {
                // Unit stands in for null: the invocation returns Any? and BlackHole.consume takes Any.
                BlackHole.consume(invocation.perIteration() ?: Unit)
            }
            null
        }.run()
    }

    companion object {

        @JvmStatic
        @Parameterized.Parameters(name = "{0}")
        fun cases(): List<Array<Any>> = DevicePlan.timedCases.map { prepared -> arrayOf(prepared.case.id, prepared) }
    }
}
