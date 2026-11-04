package io.github.junekim0007.cryptobench.benchmark.report

import io.github.junekim0007.cryptobench.settings.Metric

object MetricKeys {

    // androidx's default counters (cpuEventCounter.events), under the names it writes.
    val CPU_EVENTS = listOf("instructions", "cpuCycles", "branchMisses")

    fun of(metric: Metric): List<String> = when (metric) {
        Metric.TIME -> listOf(MetricSamples.TIME)
        Metric.ALLOCATION -> listOf(MetricSamples.ALLOCATIONS)
        Metric.CPU_EVENTS -> CPU_EVENTS
    }
}
