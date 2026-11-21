package io.github.junekim0007.cryptobench.benchmark.verify.record

import io.github.junekim0007.cryptobench.document.DocumentFields
import io.github.junekim0007.cryptobench.document.versioned.DocumentReader
import io.github.junekim0007.cryptobench.document.versioned.MapDocument
import io.github.junekim0007.cryptobench.document.versioned.YamlFiles
import java.io.File

// check.yaml: the end-to-end check's per-case records and their counts; read back by RecordDiff and lib/cryptobench/cryptobench/stages/verification/check.py.
object CheckFile {

    private const val SCHEMA = 1

    fun write(file: File, records: List<CaseRecord>, generatedFrom: Map<String, Any>): File = YamlFiles().at(file, MapDocument(SCHEMA)).write(linkedMapOf(
        "generatedFrom" to generatedFrom,
        "summary" to summary(records),
        "cases" to records.map { it.toMap() },
    ))

    fun cases(file: File): List<Map<String, Any>> = YamlFiles().readOnly(file, Cases).read()

    private object Cases : DocumentReader<List<Map<String, Any>>> {

        override val schemaVersion = SCHEMA

        override fun parse(document: Map<String, Any>): List<Map<String, Any>> = DocumentFields.sections(document, "cases")
    }

    private fun summary(records: List<CaseRecord>): Map<String, Any> {
        val oracles = LinkedHashMap<String, MutableMap<String, Int>>()
        for (record in records) {
            @Suppress("UNCHECKED_CAST")
            val verdicts = record.fields["oracles"] as? Map<String, Map<String, Any>> ?: continue
            for ((name, verdict) in verdicts) {
                val counts = oracles.getOrPut(name) { LinkedHashMap() }
                counts.merge(verdict.getValue("verdict").toString(), 1, Int::plus)
            }
        }
        return linkedMapOf(
            "cases" to records.size,
            "outcomes" to records.groupingBy { it.outcome }.eachCountTo(LinkedHashMap()),
            "oracles" to oracles,
        )
    }
}
