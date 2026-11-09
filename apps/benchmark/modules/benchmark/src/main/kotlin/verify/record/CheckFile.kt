package io.github.junekim0007.cryptobench.benchmark.verify.record

import io.github.junekim0007.cryptobench.preparation.shared.DocumentFields
import io.github.junekim0007.cryptobench.preparation.shared.DocumentFile
import java.io.File

// check.yaml: the end-to-end check's per-case records and their counts; read back by RecordDiff and apps/benchmark-runner/stages/check.py.
object CheckFile {

    private const val SCHEMA = 1

    fun write(file: File, records: List<CaseRecord>, generatedFrom: Map<String, Any>): File = DocumentFile.write(file, linkedMapOf(
        "schemaVersion" to SCHEMA,
        "generatedFrom" to generatedFrom,
        "summary" to summary(records),
        "cases" to records.map { it.toMap() },
    ))

    fun cases(file: File): List<Map<String, Any>> = DocumentFields.sections(DocumentFile.read(file, "check", SCHEMA), "cases")

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
