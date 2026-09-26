package io.github.junekim0007.cryptobench

import androidx.benchmark.junit4.BenchmarkRule
import androidx.benchmark.junit4.measureRepeated
import io.github.junekim0007.cryptobench.benchmark.run.BlackHole
import io.github.junekim0007.cryptobench.preparation.operation.Invocations
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.junit.runners.Parameterized

/**
 * One measurement per prepared case. The timed region is the invocation preparation proved runs;
 * everything a call needs beforehand is built before the timer and the per-iteration draw is
 * measured out.
 */
@RunWith(Parameterized::class)
class CryptoBenchmark(private val caseId: String, private val prepared: PreparedCase) {

    @get:Rule
    val benchmarkRule = BenchmarkRule()

    @Test
    fun measure() {
        val invocation = Invocations.of(prepared)
        benchmarkRule.measureRepeated {
            runWithMeasurementDisabled { invocation.setUp() }
            BlackHole.consume(invocation.perIteration())
        }
    }

    companion object {

        @JvmStatic
        @Parameterized.Parameters(name = "{0}")
        fun cases(): List<Array<Any>> = DevicePlan.cases.map { prepared -> arrayOf(prepared.case.id, prepared) }
    }
}
