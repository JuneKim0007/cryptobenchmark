package io.github.junekim0007.cryptobench.config.effective.dto

import io.github.junekim0007.cryptobench.config.inventory.dto.InventorySource
import io.github.junekim0007.cryptobench.config.layers.LayerStack

data class EffectiveSource(
    val global: String,
    val testSet: String,
    val inventory: String,
    val environment: InventorySource,
    // the authored layers, lowest first, and each setting's layer or "default"
    val layers: List<LayerStack.Layer> = emptyList(),
    val settings: Map<String, String> = emptyMap(),
)
