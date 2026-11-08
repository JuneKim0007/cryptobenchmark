package io.github.junekim0007.cryptobench

import io.github.junekim0007.cryptobench.benchmark.budget.NativeCleanup
import java.io.File

/** One line per timed case in native-cleanup.yaml: the paused GC and finalization its NativeBudget ran; ConvertKt joins it into the row. */
object NativeCleanups {
    // Paired with apps/benchmark-runner/device/adb.py NATIVE_CLEANUP.
    const val FILE = "native-cleanup.yaml"

    fun record(caseId: String, cleanup: NativeCleanup) {
        val fields = cleanup.toMap().entries.joinToString(", ") { (key, value) -> "$key: $value" }
        File(DevicePlan.directory, FILE).appendText("${quoted(caseId)}: {$fields}\n")
    }

    private fun quoted(text: String): String = "\"" + text.replace("\\", "\\\\").replace("\"", "\\\"") + "\""
}
