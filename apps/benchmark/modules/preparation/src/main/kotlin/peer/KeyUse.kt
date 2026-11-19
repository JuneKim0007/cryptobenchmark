package io.github.junekim0007.cryptobench.preparation.peer

import io.github.junekim0007.cryptobench.document.catalogue.FamilyCatalogue
import io.github.junekim0007.cryptobench.preparation.engine.EngineTypes
import io.github.junekim0007.cryptobench.preparation.measurement.Operation
import io.github.junekim0007.cryptobench.preparation.port.Availability
import io.github.junekim0007.cryptobench.preparation.port.DeviceCapability
import java.util.Locale

/** A generated key's use: in catalogue order, the first use-family entry whose key type, as each provider's build sees it, is the key's algorithm, Available on both providers, with an operation the harness times. */
internal class KeyUse(private val capability: DeviceCapability, private val catalogue: FamilyCatalogue = bundled) {

    class Use(val type: String, val algorithm: String, val operation: Operation)

    fun of(keyAlgorithm: String, producer: String, consumer: String): Use? {
        val builds = listOf(producer, consumer).map { catalogue.build(it, capability.platform) }
        return catalogue.entries.asSequence()
            .filter { it.family in FAMILIES }
            .filter { entry -> builds.all { keyType(entry, it).equals(keyAlgorithm, ignoreCase = true) } }
            .filter { entry -> listOf(producer, consumer).all { capability.check(it, entry.type, entry.name) == Availability.Available } }
            .firstNotNullOfOrNull { entry -> operation(entry)?.let { Use(entry.type, entry.name, it) } }
    }

    private fun keyType(entry: FamilyCatalogue.Entry, build: String?): String? = entry.section("key", build)?.get("type") as? String

    // the catalogue names operations in words (computeMac, agree); the type's timed operation is the one its word begins
    private fun operation(entry: FamilyCatalogue.Entry): Operation? = (entry.section("operations")?.get("value") as? List<*>).orEmpty().firstNotNullOfOrNull { word ->
        EngineTypes.standard().operationsOf(entry.type).firstOrNull { fold(it.name).startsWith(fold(word.toString())) }
    }

    private fun fold(name: String) = name.replace("_", "").uppercase(Locale.ROOT)

    companion object {

        val FAMILIES = listOf("cipher.secret", "cipher.pair", "signature.pair", "mac.secret", "agreement.peer")

        private val bundled: FamilyCatalogue by lazy { FamilyCatalogue.bundled(FAMILIES) }
    }
}
