package io.github.junekim0007.cryptobench.config.inventory

import io.github.junekim0007.cryptobench.config.inventory.dto.Inventory
import io.github.junekim0007.cryptobench.config.inventory.dto.InventoryEntry
import io.github.junekim0007.cryptobench.config.inventory.dto.InventorySource
import io.github.junekim0007.cryptobench.config.source.CaptureView
import io.github.junekim0007.cryptobench.config.source.TrialView
import io.github.junekim0007.cryptobench.document.names.AlgorithmNames

class InventoryBuilder {

    fun build(capture: CaptureView, trial: TrialView, files: Files): Inventory {
        val order = capture.providers + trial.entries.map { it.provider }.distinct().filter { it !in capture.providers }
        val byProvider = trial.entries.groupBy { it.provider }
        val providers = LinkedHashMap<String, Map<String, Map<String, InventoryEntry>>>()
        val warnings = mutableListOf<String>()
        for (provider in order) {
            val entries = byProvider[provider] ?: continue
            val types = LinkedHashMap<String, LinkedHashMap<String, InventoryEntry>>()
            val kept = entries.groupBy(::nameKey).mapValues { (_, spellings) -> spellings.minWith(KEPT_FIRST).name }
            for (entry in entries) {
                val winner = kept.getValue(nameKey(entry))
                if (winner != entry.name) {
                    warnings += "duplicate_name: $provider.${entry.type} $winner and ${entry.name} are one name; ${entry.name} left out"
                    continue
                }
                types.getOrPut(entry.type) { LinkedHashMap() }[entry.name] = inventoryEntry(entry.run, trial.defaultRunInputSize, capture.spellings.aliasesOf(provider, entry.type, entry.name))
            }
            providers[provider] = types
        }
        return Inventory(InventorySource(files.capture, files.trial, capture.device), providers, warnings, trial.keystore)
    }

    data class Files(val capture: String, val trial: String)

    private fun nameKey(entry: TrialView.Entry): Pair<String, Pair<String, Int?>> = entry.type to AlgorithmNames.catalog.key(entry.type, entry.name)

    private fun inventoryEntry(run: TrialView.DefaultRun, defaultRunInputSize: Int?, aliases: List<String>): InventoryEntry = InventoryEntry(
        runs = run.works,
        keySizes = listOfNotNull(run.keySize),
        inputSizes = listOfNotNull(run.inputSize?.takeIf { it != defaultRunInputSize }),
        keyAlgorithm = run.keyAlgorithm,
        keyProvider = run.keyProvider,
        providerChose = run.providerChose,
        bareName = run.bareName,
        reason = if (run.works) "" else run.error.ifEmpty { "failed" },
        aliases = aliases,
    )

    private companion object {
        // a spelling that runs, then a registered name before a transformation; the first in trial order among equals
        val KEPT_FIRST: Comparator<TrialView.Entry> = compareBy({ !it.run.works }, { it.transformation })
    }
}
