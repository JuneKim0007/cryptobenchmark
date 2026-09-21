package io.github.junekim0007.cryptobench.config.inventory

import io.github.junekim0007.cryptobench.config.inventory.dto.Inventory
import io.github.junekim0007.cryptobench.config.inventory.dto.InventoryEntry
import io.github.junekim0007.cryptobench.config.inventory.dto.InventorySource
import io.github.junekim0007.cryptobench.config.source.CaptureView
import io.github.junekim0007.cryptobench.config.source.TrialView

/** Capture × trial → inventory: every name environment called with a default key, in provider precedence order. */
class InventoryBuilder {

    fun build(capture: CaptureView, trial: TrialView, files: Files): Inventory {
        require(capture.capturedAtMillis == trial.capturedAtMillis) {
            "mismatched_trial: capture ${capture.capturedAtMillis}, trial ${trial.capturedAtMillis}"
        }
        val order = capture.providers + trial.entries.map { it.provider }.distinct().filter { it !in capture.providers }
        val byProvider = trial.entries.groupBy { it.provider }
        val providers = LinkedHashMap<String, Map<String, Map<String, InventoryEntry>>>()
        for (provider in order) {
            val entries = byProvider[provider] ?: continue
            val types = LinkedHashMap<String, LinkedHashMap<String, InventoryEntry>>()
            for (entry in entries) {
                types.getOrPut(entry.type) { LinkedHashMap() }[entry.name] = inventoryEntry(entry.run)
            }
            providers[provider] = types
        }
        return Inventory(InventorySource(files.capture, files.trial, capture.device), providers)
    }

    /** Names of the environment files, recorded in the inventory. */
    data class Files(val capture: String, val trial: String)

    private fun inventoryEntry(run: TrialView.DefaultRun): InventoryEntry = InventoryEntry(
        runs = run.works,
        keySizes = listOfNotNull(run.keySize),
        inputSizes = listOfNotNull(run.inputSize?.takeIf { it != USUAL_INPUT_SIZE }),
        keyAlgorithm = run.keyAlgorithm,
        keyProvider = run.keyProvider,
        providerChose = run.providerChose,
        bareName = run.bareName,
        reason = if (run.works) "" else run.error.ifEmpty { "failed" },
    )

    private companion object {
        /** The first size environment's default run tries; any other size it records was needed, not chosen. */
        const val USUAL_INPUT_SIZE = 1024
    }
}
