package io.github.junekim0007.cryptobench.benchmark.report.jetpack

import io.github.junekim0007.cryptobench.benchmark.budget.NativeCleanup
import io.github.junekim0007.cryptobench.benchmark.report.CaseDocument
import io.github.junekim0007.cryptobench.benchmark.report.MetricKeys
import io.github.junekim0007.cryptobench.benchmark.report.MetricSamples
import io.github.junekim0007.cryptobench.benchmark.report.ResultRow
import io.github.junekim0007.cryptobench.benchmark.report.energy.EnergyWindows
import io.github.junekim0007.cryptobench.settings.Metric

object JetpackResults {

    private const val RESOLVED_PARAMETERS = "resolvedParameters"

    // dropped: one coded line per benchmark that gave no row: not_in_plan, no_metrics, not_converted
    class Converted(val runtime: Map<String, String>, val rows: List<ResultRow>, val dropped: List<String>, val notApplied: List<String> = emptyList())

    // metrics: a set the run reports instead of each case's own; samples: a pass's own count; thermal: thermal.json's readings by case id
    fun convert(benchmarkDataText: String, preparedText: String, energy: Map<String, MetricSamples> = emptyMap(), metrics: List<String>? = null,
                samples: Int? = null, thermal: Map<String, Map<String, Any?>> = emptyMap(), cleanups: Map<String, NativeCleanup> = emptyMap()): Converted {
        val data = CaseDocument.load(benchmarkDataText)
        val prepared = CaseDocument.load(preparedText)
        val cases = CaseDocument.sections(prepared["cases"]).associateBy { case -> case["id"].toString() }
        val rows = mutableListOf<ResultRow>()
        val dropped = mutableListOf<String>()
        val notApplied = mutableListOf<String>()
        for (benchmark in CaseDocument.sections(data["benchmarks"])) {
            val id = caseIdOf(benchmark)
            val case = cases[id]
            if (case == null) {
                dropped += "not_in_plan: $id"
                continue
            }
            try {
                val measured = metricsOf(benchmark, requestedOf(id, metrics ?: case["metrics"]))
                if (measured.isEmpty()) {
                    dropped += "no_metrics: $id"
                    continue
                }
                energy[id]?.let { measured[MetricSamples.ENERGY] = it }
                val reading = thermal[id]
                rows += CaseDocument.row(case, measured, resolvedParametersOf(id, case), (benchmark[CaseDocument.SLEEP] as? Number)?.toLong(),
                    reading?.filterKeys { it in CaseDocument.THERMAL_KEYS }, reading?.get(CaseDocument.NOTE)?.toString(), gateOf(reading), cleanups[id])
                notApplied += RunCountAudit.findings(id, samples ?: CaseDocument.requestedIterations(case), measured, sampledAllocations(benchmark))
            } catch (unusable: RuntimeException) {
                dropped += "not_converted: $id: ${unusable.message ?: unusable.javaClass.simpleName}"
            }
        }
        return Converted(runtime(data), rows, dropped, notApplied)
    }

    private fun metricsOf(benchmark: Map<String, Any>, requested: List<String>): MutableMap<String, MetricSamples> {
        val blocks = CaseDocument.optionalSection(benchmark["metrics"]) ?: return LinkedHashMap()
        val metrics = LinkedHashMap<String, MetricSamples>()
        if (blocks.isEmpty()) return metrics
        for (metric in requested) {
            val block = CaseDocument.optionalSection(blocks[if (metric == MetricSamples.ALLOCATIONS && sampledAllocations(benchmark)) MetricSamples.SAMPLED_ALLOCATIONS else metric])
            val runs = CaseDocument.optionalSamples(block?.get("runs"))
            require(runs.isNotEmpty()) { "missing_field: metrics.$metric for ${caseIdOf(benchmark)}; androidx wrote ${blocks.keys}" }
            metrics[metric] = MetricSamples(runs, iterationsOf(metric, benchmark), CaseDocument.reportedStats(block))
        }
        return metrics
    }

    private fun sampledAllocations(benchmark: Map<String, Any>): Boolean =
        CaseDocument.optionalSection(benchmark["metrics"])?.containsKey(MetricSamples.SAMPLED_ALLOCATIONS) == true

    private fun requestedOf(id: String, listed: Any?): List<String> {
        val names = (listed as? List<*>)?.map { it.toString() } ?: throw IllegalArgumentException("missing_field: metrics for $id")
        return Metric.read(names, "prepared.yaml $id metrics").flatMap(MetricKeys::of)
    }

    // androidx divides allocationCount by its own unpublished inner loop before writing,
    // so one allocation run is already per operation.
    private fun iterationsOf(metric: String, benchmark: Map<String, Any>): Int =
        if (metric == MetricSamples.ALLOCATIONS) 1 else CaseDocument.iterations(benchmark["repeatIterations"])

    private fun resolvedParametersOf(id: String, case: Map<String, Any>): Map<String, Any> =
        CaseDocument.optionalSection(case[RESOLVED_PARAMETERS])
            ?: throw IllegalArgumentException("missing_field: $RESOLVED_PARAMETERS for $id; prepared.yaml predates schemaVersion 2")

    // thermal.json of apps/benchmark-runner/session/thermal_hook.py: {"cases": {"<id>": {start, end, startStatus, endStatus, note?, gate?}}}
    @Suppress("UNCHECKED_CAST")
    fun thermalOf(text: String): Map<String, Map<String, Any?>> =
        (CaseDocument.optionalSection(CaseDocument.load(text)["cases"]) ?: emptyMap()).mapValues { (_, reading) -> reading as Map<String, Any?> }

    // native-cleanup.yaml of the device's NativeCleanups: {"<id>": {everyCalls, cleanups, pausedNanos}}
    fun cleanupsOf(text: String): Map<String, NativeCleanup> =
        CaseDocument.load(text).mapNotNull { (id, fields) -> NativeCleanup.read(fields)?.let { id to it } }.toMap()

    @Suppress("UNCHECKED_CAST")
    private fun gateOf(reading: Map<String, Any?>?): Map<String, Any?>? = reading?.get(CaseDocument.GATE) as? Map<String, Any?>

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
