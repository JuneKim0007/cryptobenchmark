package io.github.junekim0007.cryptobench.config.inventory.dto

import io.github.junekim0007.cryptobench.contract.trial.KeystoreRow
import io.github.junekim0007.cryptobench.document.names.AlgorithmNames
import io.github.junekim0007.cryptobench.document.names.CaptureSpellings

data class Inventory(
    val generatedFrom: InventorySource,
    val providers: Map<String, Map<String, Map<String, InventoryEntry>>>,
    val warnings: List<String> = emptyList(),
    val keystore: List<KeystoreRow> = emptyList(),
) {

    init {
        for ((provider, types) in providers) {
            for ((type, entries) in types) {
                val same = entries.keys.groupBy { AlgorithmNames.catalog.key(type, it) }.filterValues { it.size > 1 }
                require(same.isEmpty()) { "duplicate_name: $provider.$type ${same.values.flatten()}" }
            }
        }
    }

    /** Each provider's entries that carry capture aliases, in inventory order: the capture layer config's matching reads. */
    val spellings: CaptureSpellings by lazy {
        CaptureSpellings(providers.mapValues { (_, types) ->
            types.flatMap { (type, entries) -> entries.filterValues { it.aliases.isNotEmpty() }.map { (name, entry) -> CaptureSpellings.Service(type, name, entry.aliases) } }
        })
    }

    fun entries(): List<Located> = providers.flatMap { (provider, types) ->
        types.flatMap { (type, entries) -> entries.map { (name, entry) -> Located(provider, type, name, entry) } }
    }

    data class Located(val provider: String, val type: String, val name: String, val entry: InventoryEntry)
}
