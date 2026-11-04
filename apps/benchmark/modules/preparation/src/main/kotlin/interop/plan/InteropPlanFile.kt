package io.github.junekim0007.cryptobench.preparation.interop.plan

import io.github.junekim0007.cryptobench.preparation.shared.DocumentFields.expectKeys
import io.github.junekim0007.cryptobench.preparation.shared.DocumentFields.number
import io.github.junekim0007.cryptobench.preparation.shared.DocumentFields.section
import io.github.junekim0007.cryptobench.preparation.shared.DocumentFields.sections
import io.github.junekim0007.cryptobench.preparation.shared.DocumentFields.string
import io.github.junekim0007.cryptobench.preparation.shared.DocumentFile
import java.io.File

// interop_plan.yaml is written by perf-repair from its groups.
object InteropPlanFile {

    const val NAME = "interop_plan.yaml"
    private val PAIR_KEYS = listOf("id", "group", "a", "b", "keySize", "inputSize")
    private val MEMBER_KEYS = listOf("type", "algorithm", "provider")

    fun read(file: File): List<InteropPair> = parse(DocumentFile.read(file, "interop_plan", 1))

    fun parse(document: Map<String, Any>): List<InteropPair> =
        sections(document, "pairs").mapIndexed { index, pair ->
            val path = "pairs[$index]"
            expectKeys(pair, PAIR_KEYS, path)
            try {
                InteropPair(number(pair, "id").toInt(), string(pair, "group"), member(section(pair, "a"), "$path.a"),
                            member(section(pair, "b"), "$path.b"), (pair["keySize"] as? Number)?.toInt(),
                            (pair["inputSize"] as? Number)?.toInt())
            } catch (failure: IllegalArgumentException) {
                throw IllegalArgumentException("${failure.message} at $path", failure)
            }
        }.also { pairs ->
            val ids = pairs.map { it.id }
            require(ids.size == ids.toSet().size) { "duplicate_id: interop_plan.yaml pair ids repeat" }
        }

    private fun member(document: Map<String, Any>, path: String): Member {
        expectKeys(document, MEMBER_KEYS, path)
        return Member(string(document, "type"), string(document, "algorithm"), string(document, "provider"))
    }
}
