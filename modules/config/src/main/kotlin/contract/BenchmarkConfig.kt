package io.github.junekim0007.cryptobench.config.contract

import java.util.Locale

/** default.yaml: provider → engine type → name → entry, in provider precedence order. */
data class BenchmarkConfig(
    val generatedFrom: GeneratedFrom,
    val run: RunSettings,
    val providers: Map<String, Map<String, Map<String, ConfigEntry>>>,
    val schemaVersion: Int = SCHEMA_VERSION,
) {

    init {
        for ((provider, types) in providers) {
            require(provider.isNotBlank()) { "missing_field: provider" }
            for ((type, entries) in types) {
                val folded = entries.keys.groupBy { it.uppercase(Locale.ROOT) }.filterValues { it.size > 1 }
                require(folded.isEmpty()) { "duplicate_name: $provider.$type ${folded.values.flatten()}" }
            }
        }
    }

    companion object {
        const val SCHEMA_VERSION = 1
    }
}
