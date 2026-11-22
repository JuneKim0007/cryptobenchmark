package io.github.junekim0007.cryptobench.discovery

import io.github.junekim0007.cryptobench.contract.capture.CapturedEnvironment
import java.io.File

data class ReusedRun(
    val capture: CapturedEnvironment,
    val captureFile: File,
    val trialFile: File,
    val requirementsFile: File,
)
