package io.github.junekim0007.cryptobench.config.effective.dto

import io.github.junekim0007.cryptobench.config.global.dto.Policy
import io.github.junekim0007.cryptobench.config.global.dto.RunSettings

/** effective.yaml: exactly what one run will measure, frozen. The only file preparation reads. */
data class EffectiveConfig(
    val generatedFrom: EffectiveSource,
    val run: RunSettings,
    /** Frozen here so preparation and the benchmark apply the same rule without reading global.yaml. */
    val policy: Policy,
    val providers: Map<String, Map<String, Map<String, EffectiveEntry>>>,
    val skipped: List<Skip> = emptyList(),
) {

    init {
        require(providers.values.any { types -> types.values.any { it.isNotEmpty() } }) { "nothing_selected" }
    }
}
