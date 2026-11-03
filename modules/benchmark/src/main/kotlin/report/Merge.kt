package io.github.junekim0007.cryptobench.benchmark.report

object Merge {

    // dropped: one coded line per process entry left out, or per case whose processes cannot be merged
    class Merged(val runtime: Map<String, String>, val rows: List<ResultRow>, val processes: Int, val dropped: List<String> = emptyList())

    fun merge(texts: List<String>): Merged {
        require(texts.isNotEmpty()) { "missing_field: nothing to merge" }
        val runtime = LinkedHashMap<String, String>()
        val rows = LinkedHashMap<String, ResultRow>()
        val conflicted = HashSet<String>()
        val dropped = mutableListOf<String>()
        texts.forEachIndexed { index, text ->
            val document = CaseDocument.load(text)
            CaseDocument.section(document["runtime"])
                .forEach { (key, value) -> runtime.putIfAbsent(key, value.toString()) }
            for (case in CaseDocument.sections(document["cases"])) {
                val id = case["id"].toString()
                if (id in conflicted) continue
                val row = try {
                    rowOf(case, id)
                } catch (unusable: RuntimeException) {
                    dropped += "not_merged: $id: process ${index + 1}: ${unusable.message}"
                    continue
                }
                try {
                    rows[id] = rows[id]?.mergedWith(row) ?: row
                } catch (different: IllegalArgumentException) {
                    rows.remove(id)
                    conflicted += id
                    dropped += "not_merged: $id: ${different.message}"
                }
            }
        }
        return Merged(runtime, rows.values.toList(), texts.size, dropped)
    }

    private fun rowOf(case: Map<String, Any>, id: String): ResultRow {
        val metrics = CaseDocument.metrics(case["metrics"]).ifEmpty { throw IllegalArgumentException("missing_field: metrics for $id") }
        val parameters = case[BenchmarkJson.PARAMETERS] ?: throw IllegalArgumentException("missing_field: ${BenchmarkJson.PARAMETERS} for $id")
        return CaseDocument.row(case, metrics, CaseDocument.section(parameters))
    }
}
