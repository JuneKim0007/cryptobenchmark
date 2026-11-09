package io.github.junekim0007.cryptobench

import io.github.junekim0007.cryptobench.discovery.write.ProbeDirectory
import io.github.junekim0007.cryptobench.files.FileNames
import io.github.junekim0007.cryptobench.files.StampedName
import io.github.junekim0007.cryptobench.preparation.adapter.DiscoveryCapability
import io.github.junekim0007.cryptobench.preparation.interop.InteropRun
import org.junit.Test
import java.io.File

// Run this class alone (am instrument -e class ...InteropCheck) after pushing effective.yaml, the capture, the trial and the plan.
class InteropCheck {

    @Test
    fun checksEveryPlannedPair() {
        val directory = DevicePlan.directory
        val effective = File(directory, FileNames.EFFECTIVE)
        check(effective.isFile) { "missing_file: ${effective.absolutePath}" }
        Bundled.installFrom(effective)
        val capture = newest(directory, StampedName.PROBE)
        InteropRun.run(DiscoveryCapability(capture, ProbeDirectory(directory).named(StampedName.TRIAL, capture)), File(directory, FileNames.INTEROP_PLAN), capture,
                       File(directory, FileNames.INTEROP_RESULT))
    }

    private fun newest(directory: File, prefix: String): File =
        ProbeDirectory(directory).newest(prefix)
            ?: throw IllegalStateException("missing_file: ${directory.absolutePath}/${prefix}_<stamp>.yaml")
}
