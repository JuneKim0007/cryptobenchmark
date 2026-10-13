package io.github.junekim0007.cryptobench.benchmark.report

data class MetricSamples(val runs: List<Double>, val iterations: Int, val reported: ReportedStats? = null) {

    init {
        require(runs.isNotEmpty()) { "missing_field: runs" }
        require(runs.all { it.isFinite() }) { "not_finite: runs" }
        require(iterations >= 1) { "not_positive: iterations $iterations" }
    }

    fun mergedWith(later: MetricSamples): MetricSamples = MetricSamples(runs + later.runs, iterations)

    companion object {
        const val TIME = "timeNs"

        const val ALLOCATIONS = "allocationCount"

        // From power rails via tools/energy, not from Jetpack: one run per window.
        const val ENERGY = "energyJ"

        val MEASURED = listOf(TIME, ALLOCATIONS)
    }
}
