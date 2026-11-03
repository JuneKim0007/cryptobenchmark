package io.github.junekim0007.cryptobench.benchmark.report

/** One row per case from per-pass results: the base pass's row, with each owned metric taken only from the pass that measured it. */
object PassMerge {

    class Merged(val runtime: Map<String, String>, val rows: List<ResultRow>, val dropped: List<String>)

    // owned: (metric key, that pass's benchmark.json); a key's runs never fall back to the base pass, so before/after pairs share one pass.
    fun merge(base: String, owned: List<Pair<String, String>>): Merged {
        val document = CaseDocument.load(base)
        val runtime = CaseDocument.section(document["runtime"]).mapValuesTo(LinkedHashMap()) { it.value.toString() }
        val passes = owned.map { (key, text) -> key to CaseDocument.sections(CaseDocument.load(text)["cases"]).associateBy { it["id"].toString() } }
        val rows = mutableListOf<ResultRow>()
        val dropped = mutableListOf<String>()
        for (case in CaseDocument.sections(document["cases"])) {
            val id = case["id"].toString()
            val metrics = LinkedHashMap(CaseDocument.metrics(case["metrics"]))
            for ((key, cases) in passes) {
                metrics.remove(key)
                val other = cases[id]
                if (other == null) dropped += "not_merged: $id: $key: its pass has no row" else CaseDocument.metrics(other["metrics"])[key]?.let { metrics[key] = it }
            }
            try {
                rows += CaseDocument.row(case, metrics, CaseDocument.section(case[BenchmarkJson.PARAMETERS]))
            } catch (unusable: IllegalArgumentException) {
                dropped += "not_merged: $id: ${unusable.message}"
            }
        }
        return Merged(runtime, rows, dropped)
    }
}
