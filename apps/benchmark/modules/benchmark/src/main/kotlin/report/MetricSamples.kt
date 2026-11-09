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

        // An allocation pass counts inside the timed phase, one run per sample; paired with android SampledAllocations.NAME.
        const val SAMPLED_ALLOCATIONS = "allocationSamples"

        // Per sample, not per operation: the collection run between samples with the timer stopped, and the GCs that still landed inside a sample.
        const val GC_PAUSE = "gcCleanNs"
        const val GC_COUNT = "gcCount"
        const val GC_BLOCKING = "gcBlockingCount"

        // Every timing and allocation row carries these; only the device can tell a blocking GC.
        val CLEANING = listOf(GC_PAUSE, GC_COUNT)

        // From apps/benchmark-runner/energy, not from Jetpack: one run per window, with its source and kind.
        const val ENERGY = "energyJ"
    }
}
