package io.github.junekim0007.cryptobench.benchmark.report

import org.yaml.snakeyaml.LoaderOptions
import org.yaml.snakeyaml.Yaml
import org.yaml.snakeyaml.constructor.SafeConstructor

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
            val document = section(Yaml(SafeConstructor(LoaderOptions())).load<Any?>(text))
            section(document["runtime"]).forEach { (key, value) -> runtime.putIfAbsent(key, value.toString()) }
            for (case in list(document["cases"]).map { section(it) }) {
                val row = rowOf(case)
                rows[row.id] = rows[row.id]?.mergedWith(row) ?: row
            }
        }
        return Merged(runtime, rows.values.toList(), texts.size)
    }

    private fun rowOf(case: Map<String, Any>) = ResultRow(
        id = case["id"].toString(),
        type = case["type"].toString(),
        algorithm = case["algorithm"].toString(),
        provider = case["provider"].toString(),
        operation = case["operation"].toString(),
        keySize = (case["keySize"] as? Number)?.toInt(),
        inputSize = (case["inputSize"] as? Number)?.toInt(),
        iterations = (case["iterations"] as? Number)?.toInt() ?: 1,
        nanosPerOperation = list(case["nanosPerOperation"]).map { (it as Number).toLong() },
    )

    @Suppress("UNCHECKED_CAST")
    private fun section(value: Any?): Map<String, Any> =
        value as? Map<String, Any> ?: throw IllegalArgumentException("not_a_mapping: $value")

    private fun list(value: Any?): List<Any> =
        (value as? List<*>)?.filterNotNull() ?: throw IllegalArgumentException("not_a_list: $value")
}
