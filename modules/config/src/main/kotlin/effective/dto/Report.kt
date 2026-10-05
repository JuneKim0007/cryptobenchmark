package io.github.junekim0007.cryptobench.config.effective.dto

/** What the configuration stage noticed, kept out of effective.yaml so that file holds only settings. */
data class Report(
    val runId: String?,
    val warnings: List<String> = emptyList(),
    val skipped: List<Skip> = emptyList(),
)
