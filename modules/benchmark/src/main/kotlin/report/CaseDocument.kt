package io.github.junekim0007.cryptobench.benchmark.report

import org.yaml.snakeyaml.LoaderOptions
import org.yaml.snakeyaml.Yaml
import org.yaml.snakeyaml.constructor.SafeConstructor

internal object CaseDocument {

    fun load(text: String): Map<String, Any> = section(Yaml(SafeConstructor(LoaderOptions())).load<Any?>(text))

    @Suppress("UNCHECKED_CAST")
    fun section(value: Any?): Map<String, Any> =
        value as? Map<String, Any> ?: throw IllegalArgumentException("not_a_mapping: $value")

    fun optionalSection(value: Any?): Map<String, Any>? =
        if (value == null) null else section(value)

    fun sections(value: Any?): List<Map<String, Any>> = list(value).map { element -> section(element) }

    // androidx reports ns/op as a double; truncating to an integer biases fast operations low.
    fun samples(value: Any?): List<Double> = list(value).map { sample -> (sample as Number).toDouble() }

    fun optionalSamples(value: Any?): List<Double> = if (value == null) emptyList() else samples(value)

    fun iterations(value: Any?): Int = integer(value) ?: 1

    fun metrics(value: Any?): Map<String, MetricSamples> {
        val blocks = optionalSection(value) ?: return emptyMap()
        val metrics = LinkedHashMap<String, MetricSamples>()
        for ((metric, block) in blocks) {
            val mapping = section(block)
            val runs = optionalSamples(mapping["runs"])
            if (runs.isNotEmpty()) {
                metrics[metric] = MetricSamples(runs, iterations(mapping["iterations"]), reportedStats(optionalSection(mapping["reported"])))
            }
        }
        return metrics
    }

    fun reportedStats(block: Map<String, Any>?): ReportedStats? {
        if (block == null) return null
        val values = listOf("minimum", "maximum", "median", "coefficientOfVariation").map { (block[it] as? Number)?.toDouble() ?: return null }
        return ReportedStats(values[0], values[1], values[2], values[3])
    }

    fun requestedIterations(case: Map<String, Any>): Int? = integer(optionalSection(case["harness"])?.get("iterations"))

    fun row(case: Map<String, Any>, metrics: Map<String, MetricSamples>): ResultRow = ResultRow(
        id = case["id"].toString(),
        type = case["type"].toString(),
        algorithm = case["algorithm"].toString(),
        provider = case["provider"].toString(),
        operation = case["operation"].toString(),
        keySize = integer(case["keySize"]),
        inputSize = integer(case["inputSize"]),
        keyKind = keyKind(case),
        metrics = metrics,
    )

    private fun keyKind(case: Map<String, Any>): String? =
        case["keyKind"]?.toString() ?: optionalSection(case["key"])?.get("kind")?.toString()

    private fun list(value: Any?): List<Any> =
        (value as? List<*>)?.filterNotNull() ?: throw IllegalArgumentException("not_a_list: $value")

    private fun integer(value: Any?): Int? = (value as? Number)?.toInt()
}
