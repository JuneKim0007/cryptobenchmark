package io.github.junekim0007.cryptobench

import io.github.junekim0007.cryptobench.discovery.write.ProbeDirectory
import io.github.junekim0007.cryptobench.preparation.adapter.DiscoveryCapability
import io.github.junekim0007.cryptobench.preparation.interop.InteropRun
import io.github.junekim0007.cryptobench.preparation.interop.plan.InteropPlanFile
import io.github.junekim0007.cryptobench.preparation.interop.report.InteropFile
import org.junit.Test
import java.io.File

// Run this class alone (am instrument -e class ...InteropCheck) after pushing effective.yaml, the capture, the trial and the plan.
class InteropCheck {

    @Test
    fun checksEveryPlannedPair() {
        val directory = DevicePlan.directory
        val effective = File(directory, "effective.yaml")
        check(effective.isFile) { "missing_file: ${effective.absolutePath}" }
        Bundled.installFrom(effective)
        val capture = newest(directory, "probe")
        InteropRun.run(DiscoveryCapability(capture, ProbeDirectory(directory).named("trial", capture)), File(directory, InteropPlanFile.NAME), capture,
                       File(directory, InteropFile.NAME))
    }

    private fun newest(directory: File, prefix: String): File =
        ProbeDirectory(directory).newest(prefix)
            ?: throw IllegalStateException("missing_file: ${directory.absolutePath}/${prefix}_<stamp>.yaml")
}
