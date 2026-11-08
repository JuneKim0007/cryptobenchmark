package io.github.junekim0007.cryptobench.benchmark.report

import io.github.junekim0007.cryptobench.benchmark.budget.NativeCleanup
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
                metrics[metric] = MetricSamples(runs, iterations(mapping["iterations"]), reportedStats(optionalSection(mapping["reported"])),
                    mapping["source"]?.toString(), mapping["kind"]?.toString())
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

    @Suppress("UNCHECKED_CAST")
    fun row(case: Map<String, Any>, metrics: Map<String, MetricSamples>, parameters: Map<String, Any>,
            sleep: Long? = (case[SLEEP] as? Number)?.toLong(), thermal: Map<String, Any?>? = case[THERMAL] as? Map<String, Any?>,
            note: String? = case[THERMAL_NOTE]?.toString(), gate: Map<String, Any?>? = case[GATE] as? Map<String, Any?>,
            cleanup: NativeCleanup? = NativeCleanup.read(case[NativeCleanup.FIELD])): ResultRow = ResultRow(
        id = case["id"].toString(),
        type = case["type"].toString(),
        algorithm = case["algorithm"].toString(),
        provider = case["provider"].toString(),
        operation = case["operation"].toString(),
        keySize = integer(case["keySize"]),
        inputSize = integer(case["inputSize"]),
        keyKind = keyKind(case),
        metrics = metrics,
        parameters = parameters,
        thermalThrottleSleepSeconds = sleep,
        thermal = thermal,
        thermalNote = note,
        gate = gate,
        variant = case[VARIANT]?.toString(),
        cleanup = cleanup,
    )

    const val SLEEP = "thermalThrottleSleepSeconds"
    const val THERMAL = "thermal"
    const val THERMAL_NOTE = "thermalNote"
    const val GATE = "gate"
    const val VARIANT = "variant"
    // thermal.json's per-case "note": why a reading is missing, cached, or the process's instead of the case's
    const val NOTE = "note"
    val THERMAL_KEYS = setOf("start", "end", "startStatus", "endStatus")

    private fun keyKind(case: Map<String, Any>): String? =
        case["keyKind"]?.toString() ?: optionalSection(case["key"])?.get("kind")?.toString()

    private fun list(value: Any?): List<Any> =
        (value as? List<*>)?.filterNotNull() ?: throw IllegalArgumentException("not_a_list: $value")

    private fun integer(value: Any?): Int? = (value as? Number)?.toInt()
}
