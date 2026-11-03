package io.github.junekim0007.cryptobench

import androidx.test.platform.app.InstrumentationRegistry
import io.github.junekim0007.cryptobench.benchmark.check.EnergyCapability
import io.github.junekim0007.cryptobench.benchmark.check.PlanCheck
import io.github.junekim0007.cryptobench.benchmark.check.Refusal
import io.github.junekim0007.cryptobench.benchmark.run.CaseSettings
import io.github.junekim0007.cryptobench.benchmark.run.energy.Energy
import io.github.junekim0007.cryptobench.preparation.Preparation
import io.github.junekim0007.cryptobench.preparation.adapter.DiscoveryCapability
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase
import io.github.junekim0007.cryptobench.preparation.record.PreparedFile
import io.github.junekim0007.cryptobench.discovery.bundled.BundledInstaller
import io.github.junekim0007.cryptobench.discovery.bundled.BundledProviders
import io.github.junekim0007.cryptobench.discovery.bundled.ProviderFactory
import io.github.junekim0007.cryptobench.discovery.write.ProbeDirectory
import io.github.junekim0007.cryptobench.discovery.write.YamlCodec
import io.github.junekim0007.cryptobench.preparation.report.Skip
import io.github.junekim0007.cryptobench.preparation.report.SkipFile
import java.io.File

object DevicePlan {

    private const val EFFECTIVE = "effective.yaml"
    private const val STAGE = "benchmark"
    const val CASE_ARGUMENT = "case"

    val cases: List<PreparedCase> by lazy { prepare() }

    // isolation: case names one case per instrumentation process; without the argument every timed case runs
    val timedCases: List<PreparedCase> get() {
        val named = InstrumentationRegistry.getArguments().getString(CASE_ARGUMENT)
        return cases.filter { captureOf(it) != Energy.Capture.DRY && (named == null || it.case.id == named) }
    }

    val dryCases: List<PreparedCase> get() = cases.filter { captureOf(it) == Energy.Capture.DRY }

    private fun captureOf(prepared: PreparedCase) = CaseSettings.of(prepared.case).energy.capture

    val directory: File get() = DeviceDirectory.plan

    private fun prepare(): List<PreparedCase> {
        val effective = File(directory, EFFECTIVE)
        check(effective.isFile) { "missing_file: ${effective.absolutePath}, push $EFFECTIVE with the capture and the trial" }
        val bundled = BundledProviders.read(YamlCodec().load(effective.readText()))
        BundledInstaller(ProviderFactory(InstrumentationRegistry.getInstrumentation().targetContext.classLoader)).install(bundled)
        val capture = newest("probe")
        val run = Preparation(
            DiscoveryCapability(capture, paired("trial", capture)),
            SkipFile(directory),
            PreparedFile(directory),
        ).prepare(effective)
        val checked = PlanCheck(JetpackConfig.METRICS, energyCapability = ::energyCapability).runnable(run)
        if (checked.refused.isNotEmpty()) {
            SkipFile(directory).write(run.skipped + checked.refused.map { (prepared, refusal) -> skipOf(prepared, refusal) })
        }
        return checked.runnable
    }

    private fun skipOf(prepared: PreparedCase, refusal: Refusal): Skip =
        Skip(STAGE, prepared.case.provider, prepared.case.type, prepared.case.algorithm, refusal.toString())

    private fun energyCapability(): EnergyCapability? =
        File(directory, EnergyCapability.FILE).takeIf { it.isFile }?.let { EnergyCapability.parse(it.readText()) }

    // Discovery's rule, not a plain prefix match: "probe_" would pick probe_classes_* ('c' sorts above a digit).
    private fun newest(prefix: String): File =
        ProbeDirectory(directory).newest(prefix)
            ?: throw IllegalStateException("missing_file: ${directory.absolutePath}/${prefix}_<stamp>.yaml")

    private fun paired(prefix: String, capture: File): File =
        ProbeDirectory(directory).named(prefix, capture).takeIf { it.isFile }
            ?: throw IllegalStateException("missing_file: ${ProbeDirectory(directory).named(prefix, capture).absolutePath}, the trial of ${capture.name}")
}
