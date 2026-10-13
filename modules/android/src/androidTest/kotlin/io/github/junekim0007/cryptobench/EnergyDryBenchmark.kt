package io.github.junekim0007.cryptobench

import io.github.junekim0007.cryptobench.benchmark.run.compose.CaseRuns
import io.github.junekim0007.cryptobench.benchmark.run.CaseSettings
import io.github.junekim0007.cryptobench.preparation.operation.Invocations
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase
import org.junit.Test
import org.junit.runner.RunWith
import org.junit.runners.Parameterized
import java.io.File

@RunWith(Parameterized::class)
class EnergyDryBenchmark(private val caseId: String, private val prepared: PreparedCase) {

    @Test
    fun capture() {
        val energy = CaseSettings.of(prepared.case.harness).energy
        val calls = CaseRuns.dry(caseId, energy, TraceWindowMarker, Invocations.of(prepared)).run()
        File(DevicePlan.directory, CALLS).appendText("\"$caseId\": $calls\n")
    }

    companion object {
        // Paired with scripts/energy_session.py DRY_CALLS.
        const val CALLS = "energy-dry.yaml"

        @JvmStatic
        @Parameterized.Parameters(name = "{0}")
        fun cases(): List<Array<Any>> = DevicePlan.dryCases.map { prepared -> arrayOf(prepared.case.id, prepared) }
    }
}
