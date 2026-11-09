package io.github.junekim0007.cryptobench.config.effective.dto

import io.github.junekim0007.cryptobench.config.global.dto.AnalysisSettings
import io.github.junekim0007.cryptobench.config.global.dto.BundledProvider
import io.github.junekim0007.cryptobench.config.global.dto.Policy
import io.github.junekim0007.cryptobench.config.global.dto.RunSettings
import io.github.junekim0007.cryptobench.files.StampedName

data class EffectiveConfig(
    val generatedFrom: EffectiveSource,
    val run: RunSettings,
    val policy: Policy,
    val providers: Map<String, Map<String, Map<String, EffectiveEntry>>>,
    val skipped: List<Skip> = emptyList(),
    val warnings: List<String> = emptyList(),
    val analysis: AnalysisSettings = AnalysisSettings(),
    val bundledProviders: List<BundledProvider> = emptyList(),
) {

    init {
        require(providers.values.any { types -> types.values.any { it.isNotEmpty() } }) { "nothing_selected" }
    }

    /** The discovery stamp of the capture this run was built from, e.g. 20261005T103349Z: the one id every file of the run can carry. Null for a hand-named capture. */
    val runId: String? get() = StampedName.stampOf(generatedFrom.environment.capture)
}
