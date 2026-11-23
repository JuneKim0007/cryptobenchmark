package io.github.junekim0007.cryptobench.config.global

import io.github.junekim0007.cryptobench.contract.bundled.BundledProvider
import io.github.junekim0007.cryptobench.config.global.dto.ProviderSources
import io.github.junekim0007.cryptobench.document.DocumentFields.expectKeys
import io.github.junekim0007.cryptobench.document.DocumentFields.optionalSections

object ProvidersDocument {

    private const val BUNDLED = "bundled"

    fun of(sources: ProviderSources): Map<String, Any> = linkedMapOf(BUNDLED to sources.bundled.map(BundledProvider::entry))

    fun parse(document: Map<String, Any>, path: String): ProviderSources {
        expectKeys(document, listOf(BUNDLED), path)
        return ProviderSources(BundledProvider.parseList(optionalSections(document, BUNDLED), "$path.$BUNDLED"))
    }
}
