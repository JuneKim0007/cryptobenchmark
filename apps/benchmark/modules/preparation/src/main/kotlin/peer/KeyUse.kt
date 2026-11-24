package io.github.junekim0007.cryptobench.preparation.peer

import io.github.junekim0007.cryptobench.document.catalogue.FamilyCatalogue
import io.github.junekim0007.cryptobench.document.catalogue.GroupExemplars
import io.github.junekim0007.cryptobench.document.names.AlgorithmNames
import io.github.junekim0007.cryptobench.preparation.engine.EngineTypes
import io.github.junekim0007.cryptobench.preparation.measurement.Operation
import io.github.junekim0007.cryptobench.preparation.port.Availability
import io.github.junekim0007.cryptobench.preparation.port.DeviceCapability
import java.util.Locale

/** A generated key's use: its key type from the generator's own entry, the key's name only for a generator with no entry, read through the names file's keyTypes; the families' exemplars, then catalogue order, each by type (Signature, Cipher, Mac, KeyAgreement), the first entry of that key type, as each provider's build sees it, Available on both, with an operation the harness times. */
internal class KeyUse(
    private val capability: DeviceCapability,
    private val catalogue: FamilyCatalogue = bundled,
    private val exemplars: GroupExemplars = bundledExemplars,
) {

    // builds: the producer's then the consumer's, where the use's parameters are read
    class Use(val type: String, val algorithm: String, val operation: Operation, val entry: FamilyCatalogue.Entry, val builds: List<String?>) {
        override fun toString() = "$type|$algorithm $operation"
    }

    class Found(val use: Use?, val keyTypes: List<String>)

    fun of(generator: String, generatorAlgorithm: String, keyAlgorithm: String, producer: String, consumer: String): Found {
        val own = catalogue.of(generator, generatorAlgorithm)?.takeIf { it.family in FamilyCatalogue.GENERATORS }
        val keyTypes = listOfNotNull(if (own != null) own.keyType(catalogue.build(producer, capability.platform)) else keyAlgorithm)
            .map { catalogue.names.keyType(it).name }
        return Found(keyTypes.firstNotNullOfOrNull { of(it, producer, consumer) }, keyTypes)
    }

    fun of(keyType: String, producer: String, consumer: String): Use? {
        val wanted = AlgorithmNames.fold(catalogue.names.keyType(keyType).name)
        val builds = listOf(producer, consumer).map { catalogue.build(it, capability.platform) }
        val preferred = FamilyCatalogue.KEYED.flatMap(exemplars::of).mapNotNull { id -> catalogue.of(id.substringBefore('|'), id.substringAfter('|')) }
        return listOf(preferred, catalogue.entries).asSequence().flatMap { tier -> TYPES.flatMap { type -> tier.filter { it.type == type } } }
            .filter { it.family in FamilyCatalogue.KEYED }
            .filter { entry -> builds.all { entry.keyType(it)?.let { type -> AlgorithmNames.fold(catalogue.names.keyType(type).name) } == wanted } }
            .filter { entry -> listOf(producer, consumer).all { capability.check(it, entry.type, entry.name) == Availability.Available } }
            .firstNotNullOfOrNull { entry -> operation(entry)?.let { Use(entry.type, entry.name, it, entry, builds) } }
    }

    // the catalogue names operations in words (computeMac, agree); the type's timed operation is the one its word begins
    private fun operation(entry: FamilyCatalogue.Entry): Operation? = (entry.section("operations")?.get("value") as? List<*>).orEmpty().firstNotNullOfOrNull { word ->
        EngineTypes.standard().operationsOf(entry.type).firstOrNull { plain(it.name).startsWith(plain(word.toString())) }
    }

    private fun plain(word: String) = word.replace("_", "").uppercase(Locale.ROOT)

    companion object {

        val TYPES = listOf("Signature", "Cipher", "Mac", "KeyAgreement")

        private val bundled: FamilyCatalogue by lazy { FamilyCatalogue.bundled(FamilyCatalogue.KEYED + FamilyCatalogue.GENERATORS) }
        private val bundledExemplars: GroupExemplars by lazy { GroupExemplars.bundled() }
    }
}
