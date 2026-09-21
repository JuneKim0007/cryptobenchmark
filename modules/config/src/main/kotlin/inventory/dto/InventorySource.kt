package io.github.junekim0007.cryptobench.config.inventory.dto

/** The environment files an inventory was built from. */
data class InventorySource(
    val capture: String,
    val trial: String,
    val device: Map<String, Any>,
) {

    init {
        require(capture.isNotBlank()) { "missing_field: capture" }
        require(trial.isNotBlank()) { "missing_field: trial" }
    }
}
