package io.github.junekim0007.cryptobench.config.effective.dto

data class EffectiveEntry(
    val keySizes: List<Int> = emptyList(),
    val inputSizes: List<Int> = emptyList(),
    val key: Map<String, Any> = emptyMap(),
    val parameters: Map<String, Any> = emptyMap(),
    val operations: List<String> = emptyList(),
    val providerDefaults: List<String> = emptyList(),
)
