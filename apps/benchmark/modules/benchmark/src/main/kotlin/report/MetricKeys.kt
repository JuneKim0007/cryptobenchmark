package io.github.junekim0007.cryptobench.benchmark.report

import io.github.junekim0007.cryptobench.settings.Metric

object MetricKeys {

    fun of(metric: Metric): List<String> = when (metric) {
        Metric.TIME -> listOf(MetricSamples.TIME)
        Metric.ALLOCATION -> listOf(MetricSamples.ALLOCATIONS)
    }
}
