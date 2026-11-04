package io.github.junekim0007.cryptobench.preparation.interop

import io.github.junekim0007.cryptobench.preparation.interop.plan.InteropPlanFile
import io.github.junekim0007.cryptobench.preparation.interop.report.InteropFile
import io.github.junekim0007.cryptobench.preparation.interop.report.InteropVerdict
import io.github.junekim0007.cryptobench.preparation.port.DeviceCapability
import java.io.File

object InteropRun {

    fun run(capability: DeviceCapability, plan: File, capture: File, out: File): List<InteropVerdict> {
        val verdicts = InteropPlanFile.read(plan).map(InteropOracle(capability)::check)
        InteropFile.write(out, verdicts, plan.name, capture.name)
        return verdicts
    }
}
