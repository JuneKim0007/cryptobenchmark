package io.github.junekim0007.cryptobench.preparation.peer

import io.github.junekim0007.cryptobench.document.DocumentFields
import io.github.junekim0007.cryptobench.document.YamlCodec
import io.github.junekim0007.cryptobench.preparation.engine.EngineTypes
import io.github.junekim0007.cryptobench.preparation.measurement.Operation
import io.github.junekim0007.cryptobench.preparation.port.Availability
import io.github.junekim0007.cryptobench.preparation.port.DeviceCapability
import java.util.Locale

/** A generated key's use: in catalogue order, the first use-family entry whose key type is the key's algorithm, Available on both providers, with an operation the harness times. */
internal class KeyUse(private val capability: DeviceCapability, private val entries: List<Entry> = bundled) {

    class Entry(val type: String, val algorithm: String, val keyType: String, val operations: List<String>)

    class Use(val type: String, val algorithm: String, val operation: Operation)

    fun of(keyAlgorithm: String, producer: String, consumer: String): Use? = entries.asSequence()
        .filter { it.keyType.equals(keyAlgorithm, ignoreCase = true) }
        .filter { entry -> listOf(producer, consumer).all { capability.check(it, entry.type, entry.algorithm) == Availability.Available } }
        .firstNotNullOfOrNull { entry -> operation(entry)?.let { Use(entry.type, entry.algorithm, it) } }

    // the catalogue names operations in words (computeMac, agree); the type's timed operation is the one its word begins
    private fun operation(entry: Entry): Operation? = entry.operations.firstNotNullOfOrNull { word ->
        EngineTypes.standard().operationsOf(entry.type).firstOrNull { fold(it.name).startsWith(fold(word)) }
    }

    private fun fold(name: String) = name.replace("_", "").uppercase(Locale.ROOT)

    companion object {

        val FILES = listOf("cipher.secret_catalogue.yaml", "cipher.pair_catalogue.yaml", "signature.pair_catalogue.yaml", "mac.secret_catalogue.yaml", "agreement.peer_catalogue.yaml")

        private val bundled: List<Entry> by lazy {
            parse(FILES.map { name -> KeyUse::class.java.getResource(name)?.readText() ?: throw IllegalStateException("missing_resource: $name is not beside ${KeyUse::class.java.name}") })
        }

        fun parse(texts: List<String>): List<Entry> = texts.flatMap { text ->
            DocumentFields.section(YamlCodec.DOCUMENT.load(text), "algorithms").mapNotNull { (id, value) ->
                val row = DocumentFields.asSection(value, id)
                val keyType = DocumentFields.optionalSection(row, "key")?.let { DocumentFields.optionalString(it, "type") }.orEmpty()
                val operations = DocumentFields.optionalSection(row, "operations")?.let { DocumentFields.strings(it, "value") }.orEmpty()
                if (keyType.isEmpty() || operations.isEmpty()) null else Entry(id.substringBefore('|'), id.substringAfter('|'), keyType, operations)
            }
        }
    }
}
