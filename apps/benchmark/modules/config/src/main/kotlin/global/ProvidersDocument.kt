package io.github.junekim0007.cryptobench.config.global

import io.github.junekim0007.cryptobench.config.global.dto.BundledProvider
import io.github.junekim0007.cryptobench.config.global.dto.ProviderSources
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.expectKeys
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.optionalSections
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.optionalStringOrNull
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.string
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.withPathInFailure

object ProvidersDocument {

    private const val BUNDLED = "bundled"
    private const val ARTIFACT = "artifact"
    private const val CREATE = "create"
    private const val ALIAS = "alias"

    fun of(sources: ProviderSources): Map<String, Any> = linkedMapOf(BUNDLED to bundledList(sources.bundled))

    fun parse(document: Map<String, Any>, path: String): ProviderSources {
        expectKeys(document, listOf(BUNDLED), path)
        val bundled = parseBundled(optionalSections(document, BUNDLED), "$path.$BUNDLED")
        return withPathInFailure("$path.$BUNDLED") { ProviderSources(bundled) }
    }

    fun bundledList(bundled: List<BundledProvider>): List<Map<String, Any>> = bundled.map { provider ->
        linkedMapOf<String, Any>(ARTIFACT to provider.artifact, CREATE to provider.create).apply { provider.alias?.let { put(ALIAS, it) } }
    }

    fun parseBundled(entries: List<Map<String, Any>>, path: String): List<BundledProvider> = entries.mapIndexed { index, entry ->
        val at = "$path[$index]"
        expectKeys(entry, listOf(ARTIFACT, CREATE, ALIAS), at)
        withPathInFailure(at) { BundledProvider(string(entry, ARTIFACT), string(entry, CREATE), optionalStringOrNull(entry, ALIAS)) }
    }
}
