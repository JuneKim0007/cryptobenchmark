package io.github.junekim0007.cryptobench.benchmark.verify.known

import io.github.junekim0007.cryptobench.files.FileNames
import io.github.junekim0007.cryptobench.preparation.measurement.Operation
import io.github.junekim0007.cryptobench.preparation.shared.DocumentFields
import io.github.junekim0007.cryptobench.preparation.shared.DocumentFile
import java.io.File

// Reads config/known-answers.yaml; {hex: ...} inside a parameter tree becomes bytes.
object KnownAnswerFile {

    private val KEYS = listOf("id", "source", "type", "algorithm", "aliases", "operations", "key", "parameters", "input", "output", "compare", "provider", "origin", "unexpressible")
    private val SECRET_KEYS = listOf("algorithm", "secret")
    private val PAIR_KEYS = listOf("algorithm", "private", "public")
    private const val HEX = "hex"
    private const val PREFIX = "prefix"

    fun read(file: File): List<KnownAnswer> = parse(DocumentFile.read(file, "known_answers", 1))

    fun parse(document: Map<String, Any>): List<KnownAnswer> =
        DocumentFields.sections(document, "vectors").mapIndexed { index, vector ->
            val path = "vectors[$index]"
            DocumentFields.expectKeys(vector, KEYS, path)
            val compare = DocumentFields.optionalString(vector, "compare")
            require(compare.isEmpty() || compare == PREFIX) { "unknown_compare: $compare at $path, only $PREFIX" }
            KnownAnswer(
                DocumentFields.string(vector, "id"), DocumentFields.string(vector, "source"), DocumentFields.string(vector, "type"),
                listOf(DocumentFields.string(vector, "algorithm")) + DocumentFields.optionalStrings(vector, "aliases"),
                DocumentFields.strings(vector, "operations").mapTo(LinkedHashSet()) { DocumentFields.choice<Operation>("operation", it) },
                DocumentFields.optionalSection(vector, "key").takeIf { it.isNotEmpty() }?.let { key(it, "$path.key") },
                DocumentFields.optionalSection(vector, "parameters").takeIf { it.isNotEmpty() }?.let { bytesIn(it) as Map<String, Any> },
                hex(DocumentFields.string(vector, "input")), hex(DocumentFields.string(vector, "output")), compare == PREFIX,
                DocumentFields.optionalString(vector, "provider").ifEmpty { null }, DocumentFields.optionalString(vector, "origin").ifEmpty { null },
                DocumentFields.optionalString(vector, "unexpressible").ifEmpty { null },
            )
        }.also { vectors ->
            require(vectors.map { it.id to it.provider + it.algorithms.first() }.toSet().size == vectors.size) { "duplicate_id: ${FileNames.KNOWN_ANSWERS} vector ids repeat" }
        }

    private fun key(document: Map<String, Any>, path: String): KnownAnswer.RawKey {
        val algorithm = DocumentFields.string(document, "algorithm")
        return if ("secret" in document) {
            DocumentFields.expectKeys(document, SECRET_KEYS, path)
            KnownAnswer.RawKey.Secret(algorithm, hex(DocumentFields.string(document, "secret")))
        } else {
            DocumentFields.expectKeys(document, PAIR_KEYS, path)
            KnownAnswer.RawKey.Pair(algorithm, hex(DocumentFields.string(document, "private")), hex(DocumentFields.string(document, "public")))
        }
    }

    private fun bytesIn(value: Any): Any = when {
        value is Map<*, *> && value.keys == setOf(HEX) -> hex(value[HEX] as? String ?: throw IllegalArgumentException("wrong_type: $HEX"))
        value is Map<*, *> -> value.entries.associate { (k, v) -> k.toString() to bytesIn(v!!) }
        value is List<*> -> value.map { bytesIn(it!!) }
        else -> value
    }

    fun hex(text: String): ByteArray {
        require(text.length % 2 == 0 && text.all { it.isDigit() || it.lowercaseChar() in 'a'..'f' }) { "not_hex: $text" }
        return ByteArray(text.length / 2) { text.substring(it * 2, it * 2 + 2).toInt(16).toByte() }
    }
}
