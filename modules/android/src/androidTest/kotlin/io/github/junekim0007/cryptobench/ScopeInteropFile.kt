package io.github.junekim0007.cryptobench

import java.io.File

/** scoped-interop.yaml: one line per scope with its interop verdict. */
object ScopeInteropFile {
    // Paired with scripts/device.py SCOPED_INTEROP.
    const val FILE = "scoped-interop.yaml"

    fun write(directory: File, verdicts: List<ScopeCheck.Verdict>) {
        val lines = verdicts.joinToString("") { v ->
            "${quoted(v.id)}: {interop: ${v.interop}, check: ${v.check}" + (v.reason?.let { ", reason: ${quoted(it)}" } ?: "") + "}\n"
        }
        File(directory, FILE).writeText(lines)
    }

    private fun quoted(text: String): String =
        "\"" + text.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n") + "\""
}
