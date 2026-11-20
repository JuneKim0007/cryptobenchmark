package io.github.junekim0007.cryptobench.config.entry

import io.github.junekim0007.cryptobench.config.inventory.dto.Inventory
import io.github.junekim0007.cryptobench.document.names.AlgorithmNames

/** An entry key's algorithm, provider and backing, beside its spec: written ones checked; neither algorithm nor provider written leaves the measured key. */
object KeySource {

    const val ALGORITHM = "algorithm"
    const val PROVIDER = "provider"
    const val SAME = "same"
    const val ANY = "any"
    const val BACKING = "backing"
    val KEYS = listOf(ALGORITHM, PROVIDER, BACKING)
    // where a secure key is born: tee unless strongbox is written
    val BACKINGS = listOf("tee", "strongbox")

    fun named(key: Map<String, Any>): Boolean = KEYS.mapNotNull { key[it] }.all { it is String && it.isNotBlank() }

    /** The refusal of a written key source on this device, null when it holds or nothing is written. */
    fun refusal(key: Map<String, Any>, located: Inventory.Located, inventory: Inventory): String? {
        key[BACKING]?.takeIf { it !in BACKINGS }?.let { return "invalid: key.$BACKING $it, one of $BACKINGS" }
        val written = key[PROVIDER] as String?
        if (written == null && key[ALGORITHM] == null) return null
        val candidates = when {
            written == null || written == SAME -> listOf(located.provider)
            written == ANY -> (listOf(located.provider) + inventory.providers.keys).distinct()
            else -> listOf(inventory.providers.keys.firstOrNull { AlgorithmNames.fold(it) == AlgorithmNames.fold(written) }
                ?: return "provider_not_installed: key.provider $written, installed ${inventory.providers.keys}")
        }
        val algorithm = key[ALGORITHM] as String? ?: located.entry.keyAlgorithm.ifEmpty { return "no_measured_key: ${located.type}.${located.name}" }
        return if (candidates.any { generates(inventory, it, algorithm) }) null
            else "no_key_generator: ${if (written == ANY) "no provider registers" else "${candidates.single()} registers no"} ${EngineCatalog.rows.generators.joinToString(" or ")} $algorithm"
    }

    /** The key block with a named provider in the inventory's spelling, the one preparation compares exactly; anything else as written. */
    fun spelled(key: Map<String, Any>, inventory: Inventory): Map<String, Any> {
        val written = key[PROVIDER] as? String ?: return key
        if (written == SAME || written == ANY) return key
        val installed = inventory.providers.keys.firstOrNull { AlgorithmNames.fold(it) == AlgorithmNames.fold(written) } ?: return key
        return key + (PROVIDER to installed)
    }

    // a registered name through the catalogue's spellings, or an alias the capture lists for it (an OID among them)
    private fun generates(inventory: Inventory, provider: String, algorithm: String): Boolean {
        val types = inventory.providers[provider].orEmpty()
        return EngineCatalog.rows.generators.any { type ->
            types[type].orEmpty().any { (name, entry) ->
                AlgorithmNames.catalog.matches(type, algorithm, name) || entry.aliases.any { AlgorithmNames.fold(it) == AlgorithmNames.fold(algorithm) }
            }
        }
    }
}
