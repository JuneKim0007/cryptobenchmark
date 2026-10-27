package io.github.junekim0007.cryptobench.config.global.dto

data class ProviderSources(val bundled: List<BundledProvider> = emptyList()) {

    init {
        duplicates(bundled.map { it.artifact }).let { require(it.isEmpty()) { "duplicate_artifact: $it" } }
        duplicates(bundled.mapNotNull { it.alias }).let { require(it.isEmpty()) { "duplicate_alias: $it" } }
    }

    private fun duplicates(values: List<String>): List<String> = values.groupBy { it }.filterValues { it.size > 1 }.keys.toList()
}
