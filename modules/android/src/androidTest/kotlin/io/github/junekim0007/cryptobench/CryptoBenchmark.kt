package io.github.junekim0007.cryptobench

import io.github.junekim0007.cryptobench.benchmark.run.CaseSettings
import io.github.junekim0007.cryptobench.preparation.operation.Invocations
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase
import org.junit.Test
import org.junit.runner.RunWith
import org.junit.runners.Parameterized

@RunWith(Parameterized::class)
class CryptoBenchmark(caseId: String, private val prepared: PreparedCase) : JetpackCase(caseId, CaseSettings.of(prepared.case)) {

    @Test
    fun measure() = timed { Invocations.of(prepared).perIteration }

    companion object {

        @JvmStatic
        @Parameterized.Parameters(name = "{0}")
        fun cases(): List<Array<Any>> = DevicePlan.timedCases.map { prepared -> arrayOf(prepared.case.id, prepared) }
    }
}
