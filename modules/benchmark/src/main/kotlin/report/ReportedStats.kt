package io.github.junekim0007.cryptobench.benchmark.report

data class ReportedStats(val minimum: Double, val maximum: Double, val median: Double, val coefficientOfVariation: Double) {

    init {
        require(listOf(minimum, maximum, median, coefficientOfVariation).all { it.isFinite() }) { "not_finite: reported statistics" }
    }
}
