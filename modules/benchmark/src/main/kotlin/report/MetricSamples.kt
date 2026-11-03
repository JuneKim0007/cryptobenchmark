package io.github.junekim0007.cryptobench.benchmark.report

data class MetricSamples(
    val runs: List<Double>,
    val iterations: Int,
    val reported: ReportedStats? = null,
    val source: String? = null,
    val kind: String? = null,
) {

    init {
        require(runs.isNotEmpty()) { "missing_field: runs" }
        require(runs.all { it.isFinite() }) { "not_finite: runs" }
        require(iterations >= 1) { "not_positive: iterations $iterations" }
    }

    fun mergedWith(later: MetricSamples): MetricSamples {
        require(kind == later.kind) { "energy_kinds_differ: $kind and ${later.kind}" }
        require(source == later.source) { "energy_sources_differ: $source and ${later.source}" }
        return MetricSamples(runs + later.runs, iterations, source = source, kind = kind)
    }

    companion object {
        const val TIME = "timeNs"

        const val ALLOCATIONS = "allocationCount"

        // From tools/energy, not from Jetpack: one run per window, with its source and kind.
        const val ENERGY = "energyJ"
    }
}
