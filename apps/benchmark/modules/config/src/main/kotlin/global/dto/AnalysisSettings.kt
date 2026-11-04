package io.github.junekim0007.cryptobench.config.global.dto

data class AnalysisSettings(
    val statistic: Statistic = Statistic(),
    val charts: List<Chart> = Chart.entries.toList(),
    val dir: String? = null,
    val units: Units = Units(),
) {

    init {
        require(charts.toSet().size == charts.size) { "duplicate: charts ${charts.map { it.key }}" }
        require(dir == null || dir.isNotBlank()) { "blank: dir" }
    }

    /** Which summary statistic leads in tables and charts. Both are always computed, so the choice never hides the other. */
    data class Statistic(
        val headline: Headline = Headline.AUTO,
        val meanUpToCovPercent: Double = 5.0,
    ) {

        init {
            require(meanUpToCovPercent.isFinite() && meanUpToCovPercent > 0) { "not_positive: meanUpToCovPercent $meanUpToCovPercent" }
        }
    }

    /** AUTO leads with the mean while a case's CoV is within the limit, and with the median above it. */
    enum class Headline { AUTO, MEDIAN, MEAN }

    /** The charts a run may write; naming one here is what turns it on. Defined once, so a typo fails at configuration and not after the run. */
    enum class Chart(val key: String) {
        IQR_BARS("iqrBars"),
        THROUGHPUT("throughput"),
        LATENCY("latency"),
        STABILITY("stability"),
    }

    /** Display units only: results stay ns/op and ratios unitless, so a choice changes no number a decision reads. */
    data class Units(
        val latency: LatencyUnit = LatencyUnit.MS,
        val throughput: ThroughputUnit = ThroughputUnit.MB_PER_SECOND,
    )

    enum class LatencyUnit(val key: String) { MS("ms"), US("us"), NS("ns") }

    /** MB is 10^6 bytes; MB/s and MiB/s exist only where a case has an input size, ops/s everywhere. */
    enum class ThroughputUnit(val key: String) { MB_PER_SECOND("MB/s"), MIB_PER_SECOND("MiB/s"), OPS_PER_SECOND("ops/s") }
}
