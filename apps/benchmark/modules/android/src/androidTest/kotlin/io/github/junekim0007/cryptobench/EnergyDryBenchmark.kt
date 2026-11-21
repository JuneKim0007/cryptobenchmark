package io.github.junekim0007.cryptobench

import io.github.junekim0007.cryptobench.benchmark.run.compose.CaseRuns
import io.github.junekim0007.cryptobench.benchmark.run.CaseSettings
import io.github.junekim0007.cryptobench.document.YamlLine
import io.github.junekim0007.cryptobench.files.FileNames
import io.github.junekim0007.cryptobench.preparation.operation.Invocations
import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import org.junit.AssumptionViolatedException
import org.junit.BeforeClass
import org.junit.Test
import org.junit.runner.RunWith
import org.junit.runners.Parameterized
import java.io.File

@RunWith(Parameterized::class)
class EnergyDryBenchmark(private val caseId: String, private val case: BenchmarkCase) {

    @Test
    fun capture() {
        val energy = CaseSettings.of(case).energy
        // onFailure stop already threw inside prepared(); a skip under continue is in skipped.yaml, so the dry pass still passes
        val prepared = DevicePlan.prepared(case) ?: throw AssumptionViolatedException("not_prepared: ${DevicePlan.skipOf(case)}")
        val calls = CaseRuns.dry(caseId, energy, TraceWindowMarker, Invocations.of(prepared)).run()
        File(DevicePlan.directory, FileNames.ENERGY_DRY).appendText("${YamlLine.quoted(caseId)}: $calls\n")
    }

    companion object {
        // the host's pull needs the file even when every case is skipped; the host cleared it before this run
        @JvmStatic
        @BeforeClass
        fun empty() {
            File(DevicePlan.directory, FileNames.ENERGY_DRY).writeText("")
        }

        @JvmStatic
        @Parameterized.Parameters(name = "{0}")
        fun cases(): List<Array<Any>> = DevicePlan.dryCases.map { case -> arrayOf(case.id, case) }
    }
}
