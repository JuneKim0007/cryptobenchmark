package io.github.junekim0007.cryptobench.config.effective.dto

import io.github.junekim0007.cryptobench.config.global.dto.Policy
import io.github.junekim0007.cryptobench.config.global.dto.RunSettings

data class EffectiveConfig(
    val generatedFrom: EffectiveSource,
    val run: RunSettings,
    val policy: Policy,
    val providers: Map<String, Map<String, Map<String, EffectiveEntry>>>,
    val skipped: List<Skip> = emptyList(),
    val warnings: List<String> = emptyList(),
) {

    init {
        require(providers.values.any { types -> types.values.any { it.isNotEmpty() } }) { "nothing_selected" }
    }
}
