package io.github.junekim0007.cryptobench.benchmark.report

/**
 * One process per repetition, then the samples joined: a case measured in three processes carries
 * all three processes' samples, which is the only way process-to-process variance is visible.
 */
object Merge {

    class Merged(val runtime: Map<String, String>, val rows: List<ResultRow>, val processes: Int)

    fun merge(texts: List<String>): Merged {
        require(texts.isNotEmpty()) { "missing_field: nothing to merge" }
        val runtime = LinkedHashMap<String, String>()
        val rows = LinkedHashMap<String, ResultRow>()
        for (text in texts) {
            val document = CaseDocument.load(text)
            CaseDocument.section(document["runtime"])
                .forEach { (key, value) -> runtime.putIfAbsent(key, value.toString()) }
            for (case in CaseDocument.sections(document["cases"])) {
                val row = CaseDocument.row(
                    case,
                    CaseDocument.iterations(case["iterations"]),
                    CaseDocument.samples(case["nanosPerOperation"]),
                )
                rows[row.id] = rows[row.id]?.mergedWith(row) ?: row
            }
        }
        return Merged(runtime, rows.values.toList(), texts.size)
    }
}
