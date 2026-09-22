package io.github.junekim0007.cryptobench.discovery

import io.github.junekim0007.cryptobench.discovery.contract.CapturedEnvironment
import java.io.File

data class ReusedRun(
    val capture: CapturedEnvironment,
    val captureFile: File,
    val classesFile: File,
    val trialFile: File,
)
