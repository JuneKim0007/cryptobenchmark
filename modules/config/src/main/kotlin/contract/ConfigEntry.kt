package io.github.junekim0007.cryptobench.config.contract

/**
 * One primitive under one provider. `enabled` is the user's switch; everything else is what the default run
 * observed, kept so an edit can be checked against it. Empty `inputSizes` means the run block's sizes.
 * `key` and `parameters` are opaque here: `{class, arguments}` trees that preparation binds; empty means provider default.
 */
data class ConfigEntry(
    val enabled: Boolean,
    val keySizes: List<Int> = emptyList(),
    val inputSizes: List<Int> = emptyList(),
    val key: Map<String, Any> = emptyMap(),
    val parameters: Map<String, Any> = emptyMap(),
    val keyAlgorithm: String = "",
    val keyProvider: String = "",
    val providerChose: String = "",
    val bareName: Boolean = false,
    val reason: String = "",
) {

    init {
        require(keySizes.all { it > 0 } && keySizes.size == keySizes.distinct().size) { "invalid: keySizes $keySizes" }
        require(inputSizes.all { it >= 0 } && inputSizes.size == inputSizes.distinct().size) { "invalid: inputSizes $inputSizes" }
    }
}
