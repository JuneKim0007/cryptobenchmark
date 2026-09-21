package io.github.junekim0007.cryptobench.config.effective.dto

import io.github.junekim0007.cryptobench.config.inventory.dto.InventorySource

data class EffectiveSource(
    val global: String,
    val testSet: String,
    val inventory: String,
    val environment: InventorySource,
)
