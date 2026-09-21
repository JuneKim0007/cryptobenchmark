package io.github.junekim0007.cryptobench.preparation.measurement

import java.util.zip.CRC32

internal object CaseName {

    private val UNSAFE = Regex("[^A-Za-z0-9]")

    /** Parameters change what is measured, so they change the name: a short checksum of their canonical form. */
    fun of(case: BenchmarkCase): String = listOfNotNull(
        case.type,
        case.algorithm,
        case.provider,
        case.keySize?.let { "k$it" },
        case.inputSize?.let { "i$it" },
        case.phase.name,
        parametersTag(case),
    ).joinToString("_") { part -> part.replace(UNSAFE, "-") }

    private fun parametersTag(case: BenchmarkCase): String? {
        if (case.keyParameters.isEmpty() && case.parameters.isEmpty()) {
            return null
        }
        val checksum = CRC32().apply { update((canonical(case.keyParameters) + "|" + canonical(case.parameters)).toByteArray(Charsets.UTF_8)) }
        return "p" + java.lang.Long.toHexString(checksum.value).padStart(8, '0')
    }

    private fun canonical(value: Any?): String = when (value) {
        is Map<*, *> -> value.entries.sortedBy { it.key.toString() }.joinToString(",", "{", "}") { "${it.key}=${canonical(it.value)}" }
        is List<*> -> value.joinToString(",", "[", "]") { canonical(it) }
        is ByteArray -> value.joinToString(",", "b[", "]")
        else -> value.toString()
    }
}
