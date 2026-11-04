package io.github.junekim0007.cryptobench.preparation.interop.report

import io.github.junekim0007.cryptobench.preparation.interop.plan.Member
import io.github.junekim0007.cryptobench.preparation.shared.DocumentFile
import java.io.File

// interop.yaml is read back by perf-repair, which matches each row to its plan pair by id and members.
object InteropFile {

    const val NAME = "interop.yaml"

    fun document(verdicts: List<InteropVerdict>, plan: String, capture: String): Map<String, Any> = linkedMapOf(
        "schemaVersion" to 1,
        "generatedFrom" to linkedMapOf("plan" to plan, "capture" to capture),
        "pairs" to verdicts.map { v ->
            linkedMapOf("id" to v.pair.id, "group" to v.pair.group, "a" to member(v.pair.a), "b" to member(v.pair.b),
                        "result" to v.result, "mode" to v.mode,
                        "directions" to linkedMapOf("aToB" to v.aToB.label, "bToA" to v.bToA.label), "reason" to v.reason)
        },
    )

    private fun member(m: Member): Map<String, String> =
        linkedMapOf("type" to m.type, "algorithm" to m.algorithm, "provider" to m.provider)

    fun write(file: File, verdicts: List<InteropVerdict>, plan: String, capture: String): File =
        DocumentFile.write(file, document(verdicts, plan, capture))
}
