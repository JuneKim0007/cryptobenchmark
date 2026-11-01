package io.github.junekim0007.cryptobench.benchmark.report

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
                val id = case["id"]
                val metrics = CaseDocument.metrics(case["metrics"]).ifEmpty { throw IllegalArgumentException("missing_field: metrics for $id") }
                val parameters = case[BenchmarkJson.PARAMETERS] ?: throw IllegalArgumentException("missing_field: ${BenchmarkJson.PARAMETERS} for $id")
                val row = CaseDocument.row(case, metrics, CaseDocument.section(parameters))
                rows[row.id] = rows[row.id]?.mergedWith(row) ?: row
            }
        }
        return Merged(runtime, rows.values.toList(), texts.size)
    }
}
