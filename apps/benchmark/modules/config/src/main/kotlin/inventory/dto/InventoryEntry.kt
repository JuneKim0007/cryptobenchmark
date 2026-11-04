package io.github.junekim0007.cryptobench.config.inventory.dto

data class InventoryEntry(
    val runs: Boolean,
    val keySizes: List<Int> = emptyList(),
    val inputSizes: List<Int> = emptyList(),
    val keyAlgorithm: String = "",
    val keyProvider: String = "",
    val providerChose: String = "",
    val bareName: Boolean = false,
    val reason: String = "",
) {

    init {
        require(runs == reason.isEmpty()) { "an entry carries a reason exactly when it does not run" }
        require(keySizes.all { it > 0 }) { "invalid: keySizes $keySizes" }
        require(inputSizes.all { it >= 0 }) { "invalid: inputSizes $inputSizes" }
    }
}
