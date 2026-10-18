package io.github.junekim0007.cryptobench

import io.github.junekim0007.cryptobench.settings.CpuRequest
import java.io.File

/** One line per pinned case in cpu-pins.yaml: what was asked, and the core it ran on or why it did not. */
object CorePins {
    // Paired with scripts/device.py CPU_PINS.
    const val FILE = "cpu-pins.yaml"

    fun record(caseId: String, request: CpuRequest, outcome: CorePin.Outcome) {
        val result = when (outcome) {
            is CorePin.Outcome.Applied -> "core: ${outcome.core}"
            is CorePin.Outcome.Failed -> "failed: \"${outcome.reason.replace("\"", "'")}\""
        }
        File(DevicePlan.directory, FILE).appendText("\"$caseId\": {requested: ${request.core}, required: ${request.required}, $result}\n")
    }
}
