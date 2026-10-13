package io.github.junekim0007.cryptobench.preparation.interop.report

import io.github.junekim0007.cryptobench.preparation.shared.DocumentFile
import java.io.File

// interop.yaml is read back by perf-repair as findings on its groups.
object InteropFile {

    const val NAME = "interop.yaml"

    fun document(verdicts: List<InteropVerdict>, plan: String, capture: String): Map<String, Any> = linkedMapOf(
        "schemaVersion" to 1,
        "generatedFrom" to linkedMapOf("plan" to plan, "capture" to capture),
        "verdicts" to verdicts.map { v ->
            linkedMapOf("id" to v.id, "verdict" to v.verdict, "mode" to v.mode,
                        "directions" to linkedMapOf("aToB" to v.aToB.label, "bToA" to v.bToA.label), "reason" to v.reason)
        },
    )

    fun write(file: File, verdicts: List<InteropVerdict>, plan: String, capture: String): File =
        DocumentFile.write(file, document(verdicts, plan, capture))
}
