package io.github.junekim0007.cryptobench.benchmark.report

import org.yaml.snakeyaml.LoaderOptions
import org.yaml.snakeyaml.Yaml
import org.yaml.snakeyaml.constructor.SafeConstructor

/**
 * androidx.benchmark writes `<package>-benchmarkData.json`: one entry per test, the samples under
 * `metrics.timeNs.runs`. What a case is — algorithm, provider, operation, sizes — is not in there,
 * so it is read from the `prepared.yaml` preparation wrote on the same device.
 */
object JetpackResults {

    private const val TIME_METRIC = "timeNs"

    class Converted(val runtime: Map<String, String>, val rows: List<ResultRow>, val missing: List<String>)

    fun convert(benchmarkDataText: String, preparedText: String): Converted {
        val data = load(benchmarkDataText)
        val prepared = load(preparedText)
        val cases = sections(prepared["cases"]).associateBy { it["id"].toString() }
        val rows = mutableListOf<ResultRow>()
        val missing = mutableListOf<String>()
        for (benchmark in sections(data["benchmarks"])) {
            val id = caseIdOf(benchmark)
            val case = cases[id]
            if (case == null) {
                missing += id
                continue
            }
            val metric = section(section(benchmark["metrics"])[TIME_METRIC])
            val samples = list(metric["runs"]).map { (it as Number).toLong() }
            if (samples.isEmpty()) {
                missing += id
                continue
            }
            rows += ResultRow(
                id = id,
                type = case["type"].toString(),
                algorithm = case["algorithm"].toString(),
                provider = case["provider"].toString(),
                operation = case["operation"].toString(),
                keySize = (case["keySize"] as? Number)?.toInt(),
                inputSize = (case["inputSize"] as? Number)?.toInt(),
                iterations = (benchmark["repeatIterations"] as? Number)?.toInt() ?: 1,
                nanosPerOperation = samples,
            )
        }
        return Converted(runtime(data), rows, missing)
    }

    /** The name is `<method>[<case id>]` because the parameter is the case id. */
    fun caseIdOf(benchmark: Map<String, Any>): String {
        val name = benchmark["name"].toString()
        val opened = name.indexOf('[')
        return if (opened >= 0 && name.endsWith("]")) name.substring(opened + 1, name.length - 1) else name
    }

    /**
     * What a reader needs to judge the numbers: whether the clocks were locked, whether the device
     * throttled mid-run, and what the code was compiled as.
     */
    private fun runtime(data: Map<String, Any>): Map<String, String> {
        val context = section(data["context"])
        val build = section(context["build"])
        val throttled = sections(data["benchmarks"]).sumOf { (it["thermalThrottleSleepSeconds"] as? Number)?.toLong() ?: 0L }
        return linkedMapOf(
            "model" to build["model"].toString(),
            "fingerprint" to build["fingerprint"].toString(),
            "sdkInt" to section(build["version"])["sdk"].toString(),
            "cpuLocked" to context["cpuLocked"].toString(),
            "sustainedPerformanceModeEnabled" to context["sustainedPerformanceModeEnabled"].toString(),
            "compilationMode" to context["compilationMode"].toString(),
            "thermalThrottleSleepSeconds" to throttled.toString(),
        )
    }

    private fun load(text: String): Map<String, Any> = section(Yaml(SafeConstructor(LoaderOptions())).load<Any?>(text))

    @Suppress("UNCHECKED_CAST")
    private fun section(value: Any?): Map<String, Any> =
        value as? Map<String, Any> ?: throw IllegalArgumentException("not_a_mapping: $value")

    private fun list(value: Any?): List<Any> =
        (value as? List<*>)?.filterNotNull() ?: throw IllegalArgumentException("not_a_list: $value")

    private fun sections(value: Any?): List<Map<String, Any>> = list(value).map { section(it) }
}
