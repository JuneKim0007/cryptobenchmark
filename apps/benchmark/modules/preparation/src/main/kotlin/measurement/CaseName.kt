package io.github.junekim0007.cryptobench.preparation.measurement

import java.util.zip.CRC32

internal object CaseName {

    private val UNSAFE = Regex("[^A-Za-z0-9]")

    fun of(case: BenchmarkCase): String = listOfNotNull(
        case.type,
        if (case.group.isEmpty()) case.algorithm else case.algorithm + "@" + case.group,
        case.operation.name,
        case.provider,
        case.keySize?.let { "k$it" },
        case.inputSize?.let { "i$it" },
        case.phase.name,
        parametersTag(case),
        case.variant.label,
    ).joinToString("_") { part -> part.replace(UNSAFE, "-") }

    private fun parametersTag(case: BenchmarkCase): String? {
        val identity = case.keySource.identity()
        if (case.keyParameters.isEmpty() && case.parameters.isEmpty() && identity.isEmpty()) {
            return null
        }
        // a key source that names a key joins the tag; without one the tag is the spec trees' alone
        val source = if (identity.isNotEmpty()) "|" + canonical(identity) else ""
        val checksum = CRC32().apply { update((canonical(case.keyParameters) + "|" + canonical(case.parameters) + source).toByteArray(Charsets.UTF_8)) }
        return "p" + java.lang.Long.toHexString(checksum.value).padStart(8, '0')
    }

    private fun canonical(value: Any?): String = when (value) {
        is Map<*, *> -> value.entries.sortedBy { it.key.toString() }.joinToString(",", "{", "}") { "${it.key}=${canonical(it.value)}" }
        is List<*> -> value.joinToString(",", "[", "]") { canonical(it) }
        is ByteArray -> value.joinToString(",", "b[", "]")
        else -> value.toString()
    }
}
