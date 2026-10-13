package io.github.junekim0007.cryptobench

import androidx.test.platform.app.InstrumentationRegistry
import io.github.junekim0007.cryptobench.benchmark.RefusedPlanException
import io.github.junekim0007.cryptobench.benchmark.check.EnergyCapability
import io.github.junekim0007.cryptobench.benchmark.check.PlanCheck
import io.github.junekim0007.cryptobench.benchmark.run.CaseSettings
import io.github.junekim0007.cryptobench.benchmark.run.energy.Energy
import io.github.junekim0007.cryptobench.preparation.Preparation
import io.github.junekim0007.cryptobench.preparation.adapter.DiscoveryCapability
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase
import io.github.junekim0007.cryptobench.preparation.record.PreparedFile
import io.github.junekim0007.cryptobench.discovery.write.ProbeDirectory
import io.github.junekim0007.cryptobench.preparation.report.SkipFile
import java.io.File

object DevicePlan {

    private const val DIRECTORY = "cryptobench"
    private const val EFFECTIVE = "effective.yaml"

    val cases: List<PreparedCase> by lazy { prepare() }

    val timedCases: List<PreparedCase> get() = cases.filter { captureOf(it) != Energy.Capture.DRY }

    val dryCases: List<PreparedCase> get() = cases.filter { captureOf(it) == Energy.Capture.DRY }

    private fun captureOf(prepared: PreparedCase) = CaseSettings.of(prepared.case.harness).energy.capture

    val directory: File
        get() = File(
            InstrumentationRegistry.getInstrumentation().targetContext.getExternalFilesDir(null),
            DIRECTORY,
        )

    private fun prepare(): List<PreparedCase> {
        val effective = File(directory, EFFECTIVE)
        check(effective.isFile) { "missing_file: ${effective.absolutePath}, push $EFFECTIVE with the capture and the trial" }
        val run = Preparation(
            DiscoveryCapability(newest("probe"), newest("trial")),
            SkipFile(directory),
            PreparedFile(directory),
        ).prepare(effective)
        val refusals = PlanCheck(energyCapability = ::energyCapability).check(run)
        if (refusals.isNotEmpty()) {
            throw RefusedPlanException(refusals)
        }
        return run.cases
    }

    private fun energyCapability(): EnergyCapability? =
        File(directory, EnergyCapability.FILE).takeIf { it.isFile }?.let { EnergyCapability.parse(it.readText()) }

    // Discovery's rule, not a plain prefix match: "probe_" would pick probe_classes_* ('c' sorts above a digit).
    private fun newest(prefix: String): File =
        ProbeDirectory(directory).newest(prefix)
            ?: throw IllegalStateException("missing_file: ${directory.absolutePath}/${prefix}_<stamp>.yaml")
}
