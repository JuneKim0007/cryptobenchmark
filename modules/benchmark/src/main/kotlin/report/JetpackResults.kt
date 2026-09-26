package io.github.junekim0007.cryptobench.benchmark.report

/**
 * androidx.benchmark writes `<package>-benchmarkData.json`: one entry per test, the samples under
 * `metrics.timeNs.runs`. What a case is — algorithm, provider, operation, sizes — is not in there,
 * so it is read from the `prepared.yaml` preparation wrote on the same device.
 */
object JetpackResults {

    private const val TIME_METRIC = "timeNs"

    class Converted(val runtime: Map<String, String>, val rows: List<ResultRow>, val missing: List<String>)

    fun convert(benchmarkDataText: String, preparedText: String): Converted {
        val data = CaseDocument.load(benchmarkDataText)
        val prepared = CaseDocument.load(preparedText)
        val cases = CaseDocument.sections(prepared["cases"]).associateBy { case -> case["id"].toString() }
        val rows = mutableListOf<ResultRow>()
        val missing = mutableListOf<String>()
        for (benchmark in CaseDocument.sections(data["benchmarks"])) {
            val id = caseIdOf(benchmark)
            val case = cases[id]
            if (case == null) {
                missing += id
                continue
            }
            val metric = CaseDocument.section(CaseDocument.section(benchmark["metrics"])[TIME_METRIC])
            val samples = CaseDocument.samples(metric["runs"])
            if (samples.isEmpty()) {
                missing += id
                continue
            }
            rows += CaseDocument.row(case, CaseDocument.iterations(benchmark["repeatIterations"]), samples)
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
        val context = CaseDocument.section(data["context"])
        val build = CaseDocument.section(context["build"])
        val throttled = CaseDocument.sections(data["benchmarks"])
            .sumOf { benchmark -> (benchmark["thermalThrottleSleepSeconds"] as? Number)?.toLong() ?: 0L }
        return linkedMapOf(
            "model" to build["model"].toString(),
            "fingerprint" to build["fingerprint"].toString(),
            "sdkInt" to CaseDocument.section(build["version"])["sdk"].toString(),
            "cpuLocked" to context["cpuLocked"].toString(),
            "sustainedPerformanceModeEnabled" to context["sustainedPerformanceModeEnabled"].toString(),
            "compilationMode" to context["compilationMode"].toString(),
            "thermalThrottleSleepSeconds" to throttled.toString(),
        )
    }
}
