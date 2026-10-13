package io.github.junekim0007.cryptobench.benchmark.report.jetpack

import io.github.junekim0007.cryptobench.benchmark.report.CaseDocument
import io.github.junekim0007.cryptobench.benchmark.report.MetricSamples
import io.github.junekim0007.cryptobench.benchmark.report.ResultRow
import io.github.junekim0007.cryptobench.benchmark.report.energy.EnergyWindows

object JetpackResults {

    class Converted(val runtime: Map<String, String>, val rows: List<ResultRow>, val missing: List<String>, val notApplied: List<String> = emptyList())

    fun convert(benchmarkDataText: String, preparedText: String, energy: Map<String, MetricSamples> = emptyMap()): Converted {
        val data = CaseDocument.load(benchmarkDataText)
        val prepared = CaseDocument.load(preparedText)
        val cases = CaseDocument.sections(prepared["cases"]).associateBy { case -> case["id"].toString() }
        val rows = mutableListOf<ResultRow>()
        val missing = mutableListOf<String>()
        val notApplied = mutableListOf<String>()
        for (benchmark in CaseDocument.sections(data["benchmarks"])) {
            val id = caseIdOf(benchmark)
            val case = cases[id]
            if (case == null) {
                missing += id
                continue
            }
            val metrics = metricsOf(benchmark)
            if (metrics.isEmpty()) {
                missing += id
                continue
            }
            energy[id]?.let { metrics[MetricSamples.ENERGY] = it }
            rows += CaseDocument.row(case, metrics)
            notApplied += RunCountAudit.findings(id, CaseDocument.requestedIterations(case), metrics)
        }
        return Converted(runtime(data), rows, missing, notApplied)
    }

    private fun metricsOf(benchmark: Map<String, Any>): MutableMap<String, MetricSamples> {
        val blocks = CaseDocument.optionalSection(benchmark["metrics"]) ?: return LinkedHashMap()
        val metrics = LinkedHashMap<String, MetricSamples>()
        if (blocks.isNotEmpty() && CaseDocument.optionalSection(blocks[MetricSamples.TIME]) == null) {
            throw IllegalArgumentException("missing_field: metrics.${MetricSamples.TIME} for ${caseIdOf(benchmark)}")
        }
        for (metric in MetricSamples.MEASURED) {
            val block = CaseDocument.optionalSection(blocks[metric]) ?: continue
            val runs = CaseDocument.optionalSamples(block["runs"])
            if (runs.isNotEmpty()) {
                metrics[metric] = MetricSamples(runs, iterationsOf(metric, benchmark), CaseDocument.reportedStats(block))
            }
        }
        return metrics
    }

    // androidx divides allocationCount by its own unpublished inner loop before writing,
    // so one allocation run is already per operation.
    private fun iterationsOf(metric: String, benchmark: Map<String, Any>): Int =
        if (metric == MetricSamples.TIME) CaseDocument.iterations(benchmark["repeatIterations"]) else 1

    fun caseIdOf(benchmark: Map<String, Any>): String {
        val name = benchmark["name"].toString()
        val opened = name.indexOf('[')
        return if (opened >= 0 && name.endsWith("]")) name.substring(opened + 1, name.length - 1) else name
    }

    private fun runtime(data: Map<String, Any>): Map<String, String> {
        val context = CaseDocument.section(data["context"])
        val build = CaseDocument.section(context["build"])
        val throttled = CaseDocument.sections(data["benchmarks"])
            .sumOf { benchmark -> (benchmark["thermalThrottleSleepSeconds"] as? Number)?.toLong() ?: 0L }
        return linkedMapOf(
            "model" to build["model"].toString(),
            "fingerprint" to build["fingerprint"].toString(),
            "sdkInt" to CaseDocument.section(build["version"])["sdk"].toString(),
            "jetpackCpuLocked" to context["cpuLocked"].toString(),
            "sustainedPerformanceModeEnabled" to context["sustainedPerformanceModeEnabled"].toString(),
            "compilationMode" to context["compilationMode"].toString(),
            "thermalThrottleSleepSeconds" to throttled.toString(),
        )
    }
}
