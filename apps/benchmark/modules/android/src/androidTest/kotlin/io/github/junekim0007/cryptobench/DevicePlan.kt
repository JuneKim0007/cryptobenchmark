package io.github.junekim0007.cryptobench

import io.github.junekim0007.cryptobench.benchmark.check.EnergyCapability
import io.github.junekim0007.cryptobench.benchmark.check.PlanCheck
import io.github.junekim0007.cryptobench.benchmark.check.RunnablePlan
import io.github.junekim0007.cryptobench.benchmark.run.CaseSettings
import io.github.junekim0007.cryptobench.benchmark.run.energy.Energy
import io.github.junekim0007.cryptobench.preparation.Preparation
import io.github.junekim0007.cryptobench.preparation.adapter.DiscoveryCapability
import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase
import io.github.junekim0007.cryptobench.discovery.write.ProbeDirectory
import io.github.junekim0007.cryptobench.preparation.report.Skip
import java.io.File

/**
 * The device's plan: the listed cases, each prepared only inside its own test. A process without the case argument (the listing, or one
 * process for every case) writes prepared.yaml and skipped.yaml afresh; a process given cases by name adds its own entries to them.
 */
object DevicePlan {

    private const val EFFECTIVE = "effective.yaml"

    private val plan: RunnablePlan by lazy {
        RunnablePlan(Preparation(capability), PlanCheck(JetpackConfig.METRICS, energyCapability = ::energyCapability), directory)
    }

    private val listed: List<BenchmarkCase> by lazy {
        val effective = File(directory, EFFECTIVE)
        check(effective.isFile) { "missing_file: ${effective.absolutePath}, push $EFFECTIVE with the capture and the trial" }
        Bundled.installFrom(effective)
        plan.list(effective, written = !CaseFilter.named).also { plan.stopIfSkipped() }
    }

    // The listed cases a process runs: the named ones, else every one.
    val cases: List<BenchmarkCase> get() = CaseFilter.of(listed) { it.id }

    // Preparation's skips and the plan check's refusals so far, as skipped.yaml holds them.
    val skipped: List<Skip> get() = plan.skipped

    val timedCases: List<BenchmarkCase> get() = cases.filter { captureOf(it) != Energy.Capture.DRY }

    val dryCases: List<BenchmarkCase> get() = cases.filter { captureOf(it) == Energy.Capture.DRY }

    private fun captureOf(case: BenchmarkCase) = CaseSettings.of(case).energy.capture

    val directory: File get() = DeviceDirectory.plan

    // The pushed capture and its trial: what preparation and the key planner may use on this device.
    val capability: DiscoveryCapability by lazy {
        val capture = newest("probe")
        DiscoveryCapability(capture, paired("trial", capture))
    }

    // Null when the case could not be prepared: its skip is logged and in skipped.yaml.
    fun prepared(case: BenchmarkCase): PreparedCase? = plan.prepared(case).also { if (it == null) plan.stopIfSkipped() }

    fun <T> guarded(case: BenchmarkCase, block: () -> T): T? = plan.guarded(case, RunnablePlan.CHECK, RunnablePlan.CHECK_FAILED, block = block)

    fun skipOf(case: BenchmarkCase): Skip? = plan.skipped.lastOrNull { it.reason.startsWith("${case.id}: ") }

    private fun energyCapability(): EnergyCapability? =
        File(directory, EnergyCapability.FILE).takeIf { it.isFile }?.let { EnergyCapability.parse(it.readText()) }

    private fun newest(prefix: String): File =
        ProbeDirectory(directory).newest(prefix)
            ?: throw IllegalStateException("missing_file: ${directory.absolutePath}/${prefix}_<stamp>.yaml")

    private fun paired(prefix: String, capture: File): File =
        ProbeDirectory(directory).named(prefix, capture).takeIf { it.isFile }
            ?: throw IllegalStateException("missing_file: ${ProbeDirectory(directory).named(prefix, capture).absolutePath}, the trial of ${capture.name}")
}
