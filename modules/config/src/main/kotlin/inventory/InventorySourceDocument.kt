package io.github.junekim0007.cryptobench.config.inventory

import io.github.junekim0007.cryptobench.config.inventory.dto.InventorySource
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.section
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.string

object InventorySourceDocument {

    private const val CAPTURE = "capture"
    private const val TRIAL = "trial"
    private const val DEVICE = "device"

    fun of(source: InventorySource): Map<String, Any> =
        linkedMapOf(CAPTURE to source.capture, TRIAL to source.trial, DEVICE to LinkedHashMap(source.device))

    fun parse(document: Map<String, Any>): InventorySource =
        InventorySource(string(document, CAPTURE), string(document, TRIAL), LinkedHashMap(section(document, DEVICE)))
}
