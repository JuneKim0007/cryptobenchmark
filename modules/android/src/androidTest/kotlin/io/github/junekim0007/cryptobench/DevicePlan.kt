package io.github.junekim0007.cryptobench

import androidx.test.platform.app.InstrumentationRegistry
import io.github.junekim0007.cryptobench.benchmark.RefusedPlanException
import io.github.junekim0007.cryptobench.benchmark.check.PlanCheck
import io.github.junekim0007.cryptobench.preparation.Preparation
import io.github.junekim0007.cryptobench.preparation.adapter.DiscoveryCapability
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase
import io.github.junekim0007.cryptobench.preparation.record.PreparedFile
import io.github.junekim0007.cryptobench.preparation.report.SkipFile
import java.io.File

/**
 * The plan for this device: prepared here, on the device, because the providers, the key store and
 * the default sizes are the device's own. Push the three files the run reads into
 * /sdcard/Android/data/io.github.junekim0007.cryptobench/files/cryptobench/ first.
 */
object DevicePlan {

    private const val DIRECTORY = "cryptobench"
    private const val EFFECTIVE = "effective.yaml"

    val cases: List<PreparedCase> by lazy { prepare() }

    val directory: File
        get() = File(
            InstrumentationRegistry.getInstrumentation().targetContext.getExternalFilesDir(null),
            DIRECTORY,
        )

    private fun prepare(): List<PreparedCase> {
        val effective = File(directory, EFFECTIVE)
        check(effective.isFile) { "missing_file: ${effective.absolutePath}, push $EFFECTIVE with the capture and the trial" }
        val run = Preparation(
            DiscoveryCapability(newest("probe_"), newest("trial_")),
            SkipFile(directory),
            PreparedFile(directory),
        ).prepare(effective)
        val refusals = PlanCheck().check(run)
        if (refusals.isNotEmpty()) {
            throw RefusedPlanException(refusals)
        }
        return run.cases
    }

    private fun newest(prefix: String): File =
        directory.listFiles { file -> file.name.startsWith(prefix) && file.name.endsWith(".yaml") }
            ?.maxByOrNull { it.name }
            ?: throw IllegalStateException("missing_file: ${directory.absolutePath}/$prefix*.yaml")
}
