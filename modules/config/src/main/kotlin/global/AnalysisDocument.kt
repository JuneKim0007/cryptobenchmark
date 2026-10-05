package io.github.junekim0007.cryptobench.config.global

import io.github.junekim0007.cryptobench.config.global.dto.AnalysisSettings
import io.github.junekim0007.cryptobench.config.global.dto.AnalysisSettings.Headline
import io.github.junekim0007.cryptobench.config.global.dto.AnalysisSettings.Statistic
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.expectKeys
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.optionalNumber
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.optionalSection
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.optionalString
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.withPathInFailure
import java.util.Locale

object AnalysisDocument {

    private const val STATISTIC = "statistic"
    private const val HEADLINE = "headline"
    private const val MEAN_UP_TO_COV_PERCENT = "meanUpToCovPercent"

    fun of(analysis: AnalysisSettings): Map<String, Any> = linkedMapOf(
        STATISTIC to linkedMapOf(
            HEADLINE to analysis.statistic.headline.name.lowercase(Locale.ROOT),
            MEAN_UP_TO_COV_PERCENT to analysis.statistic.meanUpToCovPercent,
        ),
    )

    fun parse(document: Map<String, Any>, path: String): AnalysisSettings {
        expectKeys(document, listOf(STATISTIC), path)
        return AnalysisSettings(optionalSection(document, STATISTIC)?.let { statistic(it, "$path.$STATISTIC") } ?: Statistic())
    }

    private fun statistic(document: Map<String, Any>, path: String): Statistic {
        expectKeys(document, listOf(HEADLINE, MEAN_UP_TO_COV_PERCENT), path)
        val defaults = Statistic()
        val named = optionalString(document, HEADLINE)
        val headline = if (named.isEmpty()) defaults.headline else Headline.values().firstOrNull { it.name.equals(named, ignoreCase = true) }
            ?: throw IllegalArgumentException("invalid: $path.$HEADLINE $named, one of ${Headline.values().map { it.name.lowercase(Locale.ROOT) }}")
        return withPathInFailure(path) {
            Statistic(headline, optionalNumber(document, MEAN_UP_TO_COV_PERCENT)?.toDouble() ?: defaults.meanUpToCovPercent)
        }
    }
}
