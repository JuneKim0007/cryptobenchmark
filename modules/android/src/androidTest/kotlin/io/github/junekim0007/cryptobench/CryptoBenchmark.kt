package io.github.junekim0007.cryptobench

import androidx.benchmark.BlackHole
import io.github.junekim0007.cryptobench.benchmark.run.CaseSettings
import io.github.junekim0007.cryptobench.preparation.operation.Invocations
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.junit.runners.Parameterized

@RunWith(Parameterized::class)
class CryptoBenchmark(private val caseId: String, private val prepared: PreparedCase) {

    private val settings = CaseSettings.of(prepared.case)

    @get:Rule
    val benchmarkRule = JetpackRule(settings)

    @Test
    fun measure() {
        val invocation = Invocations.of(prepared)
        PinnedCase.run(caseId, settings) {
            benchmarkRule.measureRepeated {
                // Unit stands in for null: the invocation returns Any? and BlackHole.consume takes Any.
                BlackHole.consume(invocation.perIteration() ?: Unit)
            }
        }
    }

    companion object {

        @JvmStatic
        @Parameterized.Parameters(name = "{0}")
        fun cases(): List<Array<Any>> = DevicePlan.timedCases.map { prepared -> arrayOf(prepared.case.id, prepared) }
    }
}
