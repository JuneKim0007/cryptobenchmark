package io.github.junekim0007.cryptobench

import android.util.Log
import io.github.junekim0007.cryptobench.settings.CpuSettings
import java.io.File

/** One line per pinned case in cpu-pins.yaml: what was asked, and the core it ran on or why it did not. */
object CorePins {
    // Paired with scripts/device.py CPU_PINS.
    const val FILE = "cpu-pins.yaml"

    fun record(caseId: String, cpu: CpuSettings, outcome: CorePin.Outcome) {
        val result = when (outcome) {
            is CorePin.Outcome.Applied -> "core: ${outcome.core}"
            is CorePin.Outcome.Failed -> "failed: ${quoted(outcome.reason)}".also { Log.w("cryptobench", "cpu_pin_failed: $caseId: ${outcome.reason}") }
        }
        File(DevicePlan.directory, FILE).appendText("${quoted(caseId)}: {requested: ${cpu.core}, required: ${cpu.isRequired}, $result}\n")
    }

    private fun quoted(text: String): String = "\"" + text.replace("\\", "\\\\").replace("\"", "\\\"") + "\""
}
