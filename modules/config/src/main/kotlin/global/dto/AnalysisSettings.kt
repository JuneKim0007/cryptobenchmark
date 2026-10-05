package io.github.junekim0007.cryptobench.config.global.dto

data class AnalysisSettings(
    val statistic: Statistic = Statistic(),
) {

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
}
