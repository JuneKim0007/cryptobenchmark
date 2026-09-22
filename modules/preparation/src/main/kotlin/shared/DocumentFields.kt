package io.github.junekim0007.cryptobench.preparation.shared

internal object DocumentFields {

    fun string(document: Map<String, Any>, key: String): String =
        field(document, key) as? String ?: wrongType(key)

    fun number(document: Map<String, Any>, key: String): Number =
        field(document, key) as? Number ?: wrongType(key)

    fun section(document: Map<String, Any>, key: String): Map<String, Any> =
        asSection(field(document, key), key)

    fun strings(document: Map<String, Any>, key: String): List<String> =
        asList(field(document, key), key).map { it as? String ?: wrongType(key) }

    fun numbers(document: Map<String, Any>, key: String): List<Int> =
        asList(field(document, key), key).map { (it as? Number ?: wrongType(key)).toInt() }

    fun optionalNumbers(document: Map<String, Any>, key: String): List<Int> =
        if (document[key] == null) emptyList() else numbers(document, key)

    fun optionalStrings(document: Map<String, Any>, key: String): List<String> =
        if (document[key] == null) emptyList() else strings(document, key)

    fun optionalSection(document: Map<String, Any>, key: String): Map<String, Any> =
        if (document[key] == null) emptyMap() else section(document, key)

    fun boolean(document: Map<String, Any>, key: String): Boolean =
        field(document, key) as? Boolean ?: wrongType(key)

    fun optionalString(document: Map<String, Any>, key: String): String =
        if (document[key] == null) "" else string(document, key)

    fun sections(document: Map<String, Any>, key: String): List<Map<String, Any>> =
        asList(field(document, key), key).map { asSection(it, key) }

    fun optionalSections(document: Map<String, Any>, key: String): List<Map<String, Any>> =
        if (document[key] == null) emptyList() else sections(document, key)

    fun asSection(value: Any, key: String): Map<String, Any> {
        @Suppress("UNCHECKED_CAST")
        return value as? Map<String, Any> ?: wrongType(key)
    }

    inline fun <reified E : Enum<E>> choice(field: String, name: String): E =
        enumValues<E>().firstOrNull { it.name.equals(name, ignoreCase = true) }
            ?: throw IllegalArgumentException("unknown_$field: $name, one of ${enumValues<E>().map { it.name }}")

    private fun field(document: Map<String, Any>, key: String): Any =
        document[key] ?: throw IllegalArgumentException("missing_field: $key")

    private fun asList(value: Any, key: String): List<Any> =
        (value as? List<*>)?.map { it ?: wrongType(key) } ?: wrongType(key)

    private fun wrongType(key: String): Nothing = throw IllegalArgumentException("wrong_type: $key")
}
