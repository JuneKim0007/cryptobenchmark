package io.github.junekim0007.cryptobench.benchmark.preparation.source

internal object ConfigFields {

    fun number(document: Map<String, Any>, key: String): Number =
        field(document, key) as? Number ?: wrongType(key)

    fun boolean(document: Map<String, Any>, key: String): Boolean =
        field(document, key) as? Boolean ?: wrongType(key)

    fun section(document: Map<String, Any>, key: String): Map<String, Any> =
        asSection(field(document, key), key)

    fun strings(document: Map<String, Any>, key: String): List<String> =
        asList(field(document, key), key).map { it as? String ?: wrongType(key) }

    fun numbers(document: Map<String, Any>, key: String): List<Int> =
        asList(field(document, key), key).map { (it as? Number ?: wrongType(key)).toInt() }

    fun optionalNumbers(document: Map<String, Any>, key: String): List<Int> =
        if (document.containsKey(key)) numbers(document, key) else emptyList()

    fun optionalSection(document: Map<String, Any>, key: String): Map<String, Any> =
        document[key]?.let { asSection(it, key) } ?: emptyMap()

    fun asSection(value: Any, key: String): Map<String, Any> {
        @Suppress("UNCHECKED_CAST")
        return value as? Map<String, Any> ?: wrongType(key)
    }

    private fun field(document: Map<String, Any>, key: String): Any =
        document[key] ?: throw IllegalArgumentException("missing_field: $key")

    private fun asList(value: Any, key: String): List<Any> =
        (value as? List<*>)?.map { it ?: wrongType(key) } ?: wrongType(key)

    private fun wrongType(key: String): Nothing = throw IllegalArgumentException("wrong_type: $key")
}
