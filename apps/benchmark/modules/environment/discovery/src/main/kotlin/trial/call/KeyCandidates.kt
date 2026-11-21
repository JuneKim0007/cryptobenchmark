package io.github.junekim0007.cryptobench.discovery.trial.call

import io.github.junekim0007.cryptobench.discovery.contract.CapturedEnvironment
import io.github.junekim0007.cryptobench.discovery.contract.ServiceKey
import io.github.junekim0007.cryptobench.document.catalogue.CatalogueOverlays
import io.github.junekim0007.cryptobench.document.catalogue.FamilyCatalogue

/** The key names a service may run on, likeliest first: a catalogued service's generators of its entry's key type as the provider's build sees it, then that key type, each followed by the registered generator or factory spellings of it, sized by the names file (a fixed size), else first at the entry's one key length, then at the generator's default; an uncatalogued one its own name and every registered generator or factory name its name contains, longest first. */
internal class KeyCandidates(private val catalogue: FamilyCatalogue, private val platform: String?, registered: List<Pair<String, String>>) {

    // fixed: the names file's size, the one the written name states
    class Candidate(val name: String, val size: Int? = null, val fixed: Boolean = size != null)

    private val generatorNames = registered.map { it.second }.distinctBy { ServiceKey.fold(it) }.sortedByDescending { it.length }

    // a provider registers a generator under its own spelling (BC ARC4 for ARCFOUR)
    private val spellings = registered.groupBy({ (type, name) -> ServiceKey.fold(catalogue.names.canonical(type, name).name) }, { it.second })

    fun of(type: String, algorithm: String, provider: String): List<Candidate> {
        val entry = entry(type, algorithm) ?: return generic(algorithm).map { Candidate(it) }
        val build = catalogue.build(provider, platform)
        val named = catalogue.names.canonical(type, algorithm).keySize
        val only = onlySize(entry, build)
        return (catalogue.generatorsOf(entry, build).map { it.name } + listOfNotNull(entry.keyType(build)))
            .flatMap { listOf(it) + spellings[ServiceKey.fold(it)].orEmpty() }
            .distinctBy { ServiceKey.fold(it) }
            .flatMap { name -> if (named != null) listOf(Candidate(name, named)) else listOfNotNull(only?.let { Candidate(name, it, fixed = false) }, Candidate(name)) }
    }

    /** The algorithm a raw key spec names: the entry's key type, else the longest registered generator name the service's name contains, else that name. */
    fun raw(type: String, algorithm: String, provider: String): String =
        entry(type, algorithm)?.keyType(catalogue.build(provider, platform)) ?: generic(algorithm).drop(1).firstOrNull() ?: algorithm

    // the one key length an entry accepts, in bits; none when it accepts several
    private fun onlySize(entry: FamilyCatalogue.Entry, build: String?): Int? =
        ((entry.section("key", build)?.get("bytes") as? List<*>)?.singleOrNull() as? Number)?.toInt()?.times(Byte.SIZE_BITS)

    private fun entry(type: String, algorithm: String): FamilyCatalogue.Entry? = catalogue.of(type, algorithm)

    private fun generic(algorithm: String): List<String> {
        val folded = ServiceKey.fold(algorithm)
        return (listOf(algorithm) + generatorNames.filter { ServiceKey.fold(it) in folded }).distinctBy { ServiceKey.fold(it) }
    }

    companion object {

        private val GENERATOR_TYPES = setOf("KEYGENERATOR", "KEYPAIRGENERATOR", "SECRETKEYFACTORY")
        private val bundled: FamilyCatalogue by lazy { FamilyCatalogue.bundled(FamilyCatalogue.KEYED + FamilyCatalogue.GENERATORS) }

        fun of(capture: CapturedEnvironment, catalogue: FamilyCatalogue = bundled): KeyCandidates = KeyCandidates(
            catalogue,
            CatalogueOverlays.platform(capture.runtime.sdkInt, capture.runtime.javaVersion),
            capture.providers.flatMap { it.services }.filter { ServiceKey.fold(it.type) in GENERATOR_TYPES }.map { it.type to it.algorithm },
        )
    }
}
