package io.github.junekim0007.cryptobench.config.inventory

import io.github.junekim0007.cryptobench.config.inventory.dto.Inventory
import io.github.junekim0007.cryptobench.config.inventory.dto.InventoryEntry
import io.github.junekim0007.cryptobench.config.inventory.dto.InventorySource
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.boolean
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.optionalBoolean
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.optionalNumbers
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.optionalString
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.section
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.string
import io.github.junekim0007.cryptobench.config.yaml.DocumentHandler
import io.github.junekim0007.cryptobench.config.yaml.ProviderTree

/** inventory.yaml. */
object InventoryDocument : DocumentHandler<Inventory> {

    override val schemaVersion: Int = 1

    private const val GENERATED_FROM = "generatedFrom"
    private const val CAPTURE = "capture"
    private const val TRIAL = "trial"
    private const val DEVICE = "device"
    private const val PROVIDERS = "providers"
    private const val RUNS = "runs"
    private const val KEY_SIZES = "keySizes"
    private const val INPUT_SIZES = "inputSizes"
    private const val KEY_ALGORITHM = "keyAlgorithm"
    private const val KEY_PROVIDER = "keyProvider"
    private const val PROVIDER_CHOSE = "providerChose"
    private const val BARE_NAME = "bareName"
    private const val REASON = "reason"

    override fun of(value: Inventory): Map<String, Any> = linkedMapOf(
        GENERATED_FROM to linkedMapOf(CAPTURE to value.generatedFrom.capture, TRIAL to value.generatedFrom.trial, DEVICE to LinkedHashMap(value.generatedFrom.device)),
        PROVIDERS to ProviderTree.of(value.providers) { entry -> entry(entry) },
    )

    override fun parse(document: Map<String, Any>): Inventory {
        val source = section(document, GENERATED_FROM)
        return Inventory(
            generatedFrom = InventorySource(string(source, CAPTURE), string(source, TRIAL), LinkedHashMap(section(source, DEVICE))),
            providers = ProviderTree.parse(section(document, PROVIDERS), PROVIDERS) { entry, _ -> entryOf(entry) },
        )
    }

    private fun entry(entry: InventoryEntry): Map<String, Any> = LinkedHashMap<String, Any>().apply {
        put(RUNS, entry.runs)
        if (entry.keySizes.isNotEmpty()) put(KEY_SIZES, entry.keySizes)
        if (entry.inputSizes.isNotEmpty()) put(INPUT_SIZES, entry.inputSizes)
        if (entry.keyAlgorithm.isNotEmpty()) put(KEY_ALGORITHM, entry.keyAlgorithm)
        if (entry.keyProvider.isNotEmpty()) put(KEY_PROVIDER, entry.keyProvider)
        if (entry.providerChose.isNotEmpty()) put(PROVIDER_CHOSE, entry.providerChose)
        if (entry.bareName) put(BARE_NAME, true)
        if (entry.reason.isNotEmpty()) put(REASON, entry.reason)
    }

    private fun entryOf(document: Map<String, Any>): InventoryEntry = InventoryEntry(
        runs = boolean(document, RUNS),
        keySizes = optionalNumbers(document, KEY_SIZES),
        inputSizes = optionalNumbers(document, INPUT_SIZES),
        keyAlgorithm = optionalString(document, KEY_ALGORITHM),
        keyProvider = optionalString(document, KEY_PROVIDER),
        providerChose = optionalString(document, PROVIDER_CHOSE),
        bareName = optionalBoolean(document, BARE_NAME),
        reason = optionalString(document, REASON),
    )
}
