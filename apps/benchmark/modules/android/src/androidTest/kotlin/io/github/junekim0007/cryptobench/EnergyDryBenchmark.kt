package io.github.junekim0007.cryptobench

import io.github.junekim0007.cryptobench.benchmark.run.compose.CaseRuns
import io.github.junekim0007.cryptobench.benchmark.run.CaseSettings
import io.github.junekim0007.cryptobench.files.FileNames
import io.github.junekim0007.cryptobench.preparation.operation.Invocations
import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import org.junit.Test
import org.junit.runner.RunWith
import org.junit.runners.Parameterized
import java.io.File

@RunWith(Parameterized::class)
class EnergyDryBenchmark(private val caseId: String, private val case: BenchmarkCase) {

    @Test
    fun capture() {
        val energy = CaseSettings.of(case).energy
        val prepared = DevicePlan.prepared(case) ?: error("not_prepared: ${DevicePlan.skipOf(case)}")
        val calls = CaseRuns.dry(caseId, energy, TraceWindowMarker, Invocations.of(prepared)).run()
        File(DevicePlan.directory, FileNames.ENERGY_DRY).appendText("\"$caseId\": $calls\n")
    }

    companion object {
        @JvmStatic
        @Parameterized.Parameters(name = "{0}")
        fun cases(): List<Array<Any>> = DevicePlan.dryCases.map { case -> arrayOf(case.id, case) }
    }
}
