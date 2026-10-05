package io.github.junekim0007.cryptobench.config.global

import io.github.junekim0007.cryptobench.config.global.dto.AnalysisSettings
import io.github.junekim0007.cryptobench.config.global.dto.AnalysisSettings.Chart
import io.github.junekim0007.cryptobench.config.global.dto.AnalysisSettings.Headline
import io.github.junekim0007.cryptobench.config.global.dto.AnalysisSettings.Statistic
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.choice
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.expectKeys
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.optionalNumber
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.optionalSection
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.optionalString
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.optionalStringOrNull
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.optionalStrings
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.withPathInFailure
import java.util.Locale

object AnalysisDocument {

    private const val STATISTIC = "statistic"
    private const val CHARTS = "charts"
    private const val DIR = "dir"
    private const val HEADLINE = "headline"
    private const val MEAN_UP_TO_COV_PERCENT = "meanUpToCovPercent"

    fun of(analysis: AnalysisSettings): Map<String, Any> = linkedMapOf(
        STATISTIC to linkedMapOf(
            HEADLINE to analysis.statistic.headline.name.lowercase(Locale.ROOT),
            MEAN_UP_TO_COV_PERCENT to analysis.statistic.meanUpToCovPercent,
        ),
        CHARTS to analysis.charts.map { it.key },
    ).apply { analysis.dir?.let { put(DIR, it) } }

    fun parse(document: Map<String, Any>, path: String): AnalysisSettings {
        expectKeys(document, listOf(STATISTIC, CHARTS, DIR), path)
        val defaults = AnalysisSettings()
        val statistic = optionalSection(document, STATISTIC)?.let { statistic(it, "$path.$STATISTIC") } ?: defaults.statistic
        val charts = if (CHARTS in document) charts(optionalStrings(document, CHARTS), "$path.$CHARTS") else defaults.charts
        return withPathInFailure(path) { AnalysisSettings(statistic, charts, optionalStringOrNull(document, DIR)) }
    }

    private fun charts(names: List<String>, path: String): List<Chart> = names.map { name -> choice(path, name, Chart.entries) { it.key } }

    private fun statistic(document: Map<String, Any>, path: String): Statistic {
        expectKeys(document, listOf(HEADLINE, MEAN_UP_TO_COV_PERCENT), path)
        val defaults = Statistic()
        val named = optionalString(document, HEADLINE)
        val headline = if (named.isEmpty()) defaults.headline else choice("$path.$HEADLINE", named, Headline.values().toList()) { it.name.lowercase(Locale.ROOT) }
        return withPathInFailure(path) {
            Statistic(headline, optionalNumber(document, MEAN_UP_TO_COV_PERCENT)?.toDouble() ?: defaults.meanUpToCovPercent)
        }
    }
}
