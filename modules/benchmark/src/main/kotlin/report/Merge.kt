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
                val row = CaseDocument.row(case, metricsOf(case))
                rows[row.id] = rows[row.id]?.mergedWith(row) ?: row
            }
        }
        return Merged(runtime, rows.values.toList(), texts.size)
    }

    // Files written before `metrics` existed carry only the flat iterations/nanosPerOperation pair.
    private fun metricsOf(case: Map<String, Any>): Map<String, MetricSamples> {
        val metrics = CaseDocument.metrics(case["metrics"])
        if (metrics.isNotEmpty()) {
            return metrics
        }
        return linkedMapOf(
            MetricSamples.TIME to MetricSamples(
                CaseDocument.samples(case["nanosPerOperation"]),
                CaseDocument.iterations(case["iterations"]),
            ),
        )
    }
}
