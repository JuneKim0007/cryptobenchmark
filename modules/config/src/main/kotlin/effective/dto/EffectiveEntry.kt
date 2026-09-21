package io.github.junekim0007.cryptobench.config.effective.dto

/** One primitive that will run, fully resolved. `providerDefaults` names what was left for the provider to choose. */
data class EffectiveEntry(
    val keySizes: List<Int> = emptyList(),
    /** Empty means the run section's sizes. */
    val inputSizes: List<Int> = emptyList(),
    val key: Map<String, Any> = emptyMap(),
    val parameters: Map<String, Any> = emptyMap(),
    val providerDefaults: List<String> = emptyList(),
)
