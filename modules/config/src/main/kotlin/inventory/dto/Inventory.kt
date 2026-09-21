package io.github.junekim0007.cryptobench.config.inventory.dto

import java.util.Locale

/** inventory.yaml: provider → engine type → name → what the device showed. Generated, never edited. */
data class Inventory(
    val generatedFrom: InventorySource,
    val providers: Map<String, Map<String, Map<String, InventoryEntry>>>,
) {

    init {
        for ((provider, types) in providers) {
            for ((type, entries) in types) {
                val folded = entries.keys.groupBy { it.uppercase(Locale.ROOT) }.filterValues { it.size > 1 }
                require(folded.isEmpty()) { "duplicate_name: $provider.$type ${folded.values.flatten()}" }
            }
        }
    }

    /** Every entry, flat, in provider precedence order. */
    fun entries(): List<Located> = providers.flatMap { (provider, types) ->
        types.flatMap { (type, entries) -> entries.map { (name, entry) -> Located(provider, type, name, entry) } }
    }

    data class Located(val provider: String, val type: String, val name: String, val entry: InventoryEntry)
}
