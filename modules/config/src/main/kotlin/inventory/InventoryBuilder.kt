package io.github.junekim0007.cryptobench.config.inventory

import io.github.junekim0007.cryptobench.config.inventory.dto.Inventory
import io.github.junekim0007.cryptobench.config.inventory.dto.InventoryEntry
import io.github.junekim0007.cryptobench.config.inventory.dto.InventorySource
import io.github.junekim0007.cryptobench.config.names.AlgorithmNames
import io.github.junekim0007.cryptobench.config.source.CaptureView
import io.github.junekim0007.cryptobench.config.source.TrialView

class InventoryBuilder {

    fun build(capture: CaptureView, trial: TrialView, files: Files): Inventory {
        require(capture.capturedAtMillis == trial.capturedAtMillis) {
            "mismatched_trial: capture ${capture.capturedAtMillis}, trial ${trial.capturedAtMillis}"
        }
        val order = capture.providers + trial.entries.map { it.provider }.distinct().filter { it !in capture.providers }
        val byProvider = trial.entries.groupBy { it.provider }
        val providers = LinkedHashMap<String, Map<String, Map<String, InventoryEntry>>>()
        val warnings = mutableListOf<String>()
        for (provider in order) {
            val entries = byProvider[provider] ?: continue
            val types = LinkedHashMap<String, LinkedHashMap<String, InventoryEntry>>()
            val kept = HashMap<Pair<String, Pair<String, Int?>>, String>()
            for (entry in entries) {
                val first = kept.putIfAbsent(entry.type to AlgorithmNames.catalog.key(entry.type, entry.name), entry.name)
                if (first != null && first != entry.name) {
                    warnings += "duplicate_name: $provider.${entry.type} $first and ${entry.name} are one name; ${entry.name} left out"
                    continue
                }
                types.getOrPut(entry.type) { LinkedHashMap() }[entry.name] = inventoryEntry(entry.run, trial.defaultRunInputSize)
            }
            providers[provider] = types
        }
        return Inventory(InventorySource(files.capture, files.trial, capture.device), providers, warnings)
    }

    data class Files(val capture: String, val trial: String)

    private fun inventoryEntry(run: TrialView.DefaultRun, defaultRunInputSize: Int?): InventoryEntry = InventoryEntry(
        runs = run.works,
        keySizes = listOfNotNull(run.keySize),
        inputSizes = listOfNotNull(run.inputSize?.takeIf { it != defaultRunInputSize }),
        keyAlgorithm = run.keyAlgorithm,
        keyProvider = run.keyProvider,
        providerChose = run.providerChose,
        bareName = run.bareName,
        reason = if (run.works) "" else run.error.ifEmpty { "failed" },
    )
}
