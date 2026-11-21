package io.github.junekim0007.cryptobench.preparation.interop.report

import io.github.junekim0007.cryptobench.preparation.interop.plan.Member
import io.github.junekim0007.cryptobench.document.versioned.MapDocument
import io.github.junekim0007.cryptobench.document.versioned.YamlFiles
import java.io.File

// interop.yaml is read back by perf-repair, which matches each row to its plan pair by id and members.
object InteropFile {


    fun document(verdicts: List<InteropVerdict>, plan: String, capture: String): Map<String, Any> = linkedMapOf(
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
        YamlFiles().at(file, MapDocument(1)).write(document(verdicts, plan, capture))
}
