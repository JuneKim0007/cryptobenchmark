package io.github.junekim0007.cryptobench.discovery.trial.call

import io.github.junekim0007.cryptobench.contract.capture.CapturedEnvironment
import io.github.junekim0007.cryptobench.discovery.trial.EngineTypes
import io.github.junekim0007.cryptobench.document.catalogue.CatalogueOverlays
import io.github.junekim0007.cryptobench.document.catalogue.FamilyCatalogue
import io.github.junekim0007.cryptobench.document.names.AlgorithmNames

/** The key names a service may run on, likeliest first: a catalogued service's generators of its entry's key type as the provider's build sees it, then that key type, each followed by the registered generator or factory spellings of it, sized by the names file (a fixed size), else first at the entry's one key length, then at the generator's default, then with the entry's built [KeyGenerationSpec]; an uncatalogued one its own name and every registered generator or factory name its name contains, longest first. */
internal class KeyCandidates(private val catalogue: FamilyCatalogue, private val platform: String?, registered: List<Pair<String, String>>) {

    // fixed: the names file's size, the one the written name states; spec: the entry's key spec, tried after the name alone
    class Candidate(val name: String, val size: Int? = null, val fixed: Boolean = size != null, val spec: KeyGenerationSpec.Built? = null)

    private val generatorNames = registered.map { it.second }.distinctBy { AlgorithmNames.fold(it) }.sortedByDescending { it.length }

    // a provider registers a generator under its own spelling (BC ARC4 for ARCFOUR)
    private val spellings = registered.groupBy({ (type, name) -> AlgorithmNames.fold(catalogue.names.canonical(type, name).name) }, { it.second })

    fun of(type: String, algorithm: String, provider: String): List<Candidate> {
        val entry = entry(type, algorithm) ?: return generic(algorithm).map { Candidate(it) }
        val build = catalogue.build(provider, platform)
        val named = catalogue.names.canonical(type, algorithm).keySize
        val only = onlySize(entry, build)
        val spec = keyGeneration(entry, build) as? KeyGenerationSpec.Built
        return (catalogue.generatorsOf(entry, build).map { it.name } + listOfNotNull(entry.keyType(build)))
            .flatMap { listOf(it) + spellings[AlgorithmNames.fold(it)].orEmpty() }
            .distinctBy { AlgorithmNames.fold(it) }
            .flatMap { name ->
                (if (named != null) listOf(Candidate(name, named)) else listOfNotNull(only?.let { Candidate(name, it, fixed = false) }, Candidate(name))) +
                    listOfNotNull(spec?.let { Candidate(name, spec = it) })
            }
    }

    /** The entry's key-generation spec as the provider's build sees it; [KeyGenerationSpec.None] for an uncatalogued service. */
    fun keyGeneration(type: String, algorithm: String, provider: String): KeyGenerationSpec =
        entry(type, algorithm)?.let { keyGeneration(it, catalogue.build(provider, platform)) } ?: KeyGenerationSpec.None

    private val specs = HashMap<kotlin.Pair<String, String?>, KeyGenerationSpec>()

    private fun keyGeneration(entry: FamilyCatalogue.Entry, build: String?): KeyGenerationSpec =
        specs.getOrPut(entry.id to build) { KeyGenerationSpec.of(entry, build) }

    /** The algorithm a raw key spec names: the entry's key type, else the longest registered generator name the service's name contains, else that name. */
    fun raw(type: String, algorithm: String, provider: String): String =
        entry(type, algorithm)?.keyType(catalogue.build(provider, platform)) ?: generic(algorithm).drop(1).firstOrNull() ?: algorithm

    // the one key length an entry accepts, in bits; none when it accepts several
    private fun onlySize(entry: FamilyCatalogue.Entry, build: String?): Int? =
        ((entry.section("key", build)?.get("bytes") as? List<*>)?.singleOrNull() as? Number)?.toInt()?.times(Byte.SIZE_BITS)

    private fun entry(type: String, algorithm: String): FamilyCatalogue.Entry? = catalogue.of(type, algorithm)

    private fun generic(algorithm: String): List<String> {
        val folded = AlgorithmNames.fold(algorithm)
        return (listOf(algorithm) + generatorNames.filter { AlgorithmNames.fold(it) in folded }).distinctBy { AlgorithmNames.fold(it) }
    }

    companion object {

        private val bundled: FamilyCatalogue by lazy { FamilyCatalogue.bundled(FamilyCatalogue.KEYED + FamilyCatalogue.GENERATORS) }

        fun of(capture: CapturedEnvironment, catalogue: FamilyCatalogue = bundled): KeyCandidates = KeyCandidates(
            catalogue,
            CatalogueOverlays.platform(capture.runtime.sdkInt, capture.runtime.javaVersion),
            capture.providers.flatMap { it.services }.filter { AlgorithmNames.fold(it.type) in EngineTypes.KEY_MAKERS }.map { it.type to it.algorithm },
        )
    }
}
