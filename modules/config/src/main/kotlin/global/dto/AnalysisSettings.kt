package io.github.junekim0007.cryptobench.config.global.dto

data class AnalysisSettings(
    val statistic: Statistic = Statistic(),
    val charts: List<Chart> = Chart.entries.toList(),
    val dir: String? = null,
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
}
