package io.github.junekim0007.cryptobench.discovery.write

internal object DocumentFields {

    fun string(document: Map<String, Any>, key: String): String =
        field(document, key) as? String ?: wrongType(key)

    fun optionalString(document: Map<String, Any>, key: String): String =
        document[key]?.let { it as? String ?: wrongType(key) } ?: ""

    fun number(document: Map<String, Any>, key: String): Number =
        field(document, key) as? Number ?: wrongType(key)

    fun boolean(document: Map<String, Any>, key: String): Boolean =
        field(document, key) as? Boolean ?: wrongType(key)

    fun optionalNumber(document: Map<String, Any>, key: String): Number? =
        document[key]?.let { it as? Number ?: wrongType(key) }

    fun optionalBoolean(document: Map<String, Any>, key: String): Boolean =
        document[key]?.let { it as? Boolean ?: wrongType(key) } ?: false

    fun section(document: Map<String, Any>, key: String): Map<String, Any> =
        asSection(field(document, key), key)

    fun optionalSection(document: Map<String, Any>, key: String): Map<String, Any>? =
        document[key]?.let { asSection(it, key) }

    fun sections(document: Map<String, Any>, key: String): List<Map<String, Any>> =
        asList(field(document, key), key).map { asSection(it, key) }

    fun optionalSections(document: Map<String, Any>, key: String): List<Map<String, Any>> =
        if (document.containsKey(key)) sections(document, key) else emptyList()

    fun optionalStrings(document: Map<String, Any>, key: String): List<String> =
        document[key]?.let { value -> asList(value, key).map { element -> element as? String ?: wrongType(key) } }
            ?: emptyList()

    private fun field(document: Map<String, Any>, key: String): Any =
        document[key] ?: throw IllegalArgumentException("missing_field: $key")

    @Suppress("UNCHECKED_CAST")
    private fun asSection(value: Any, key: String): Map<String, Any> =
        value as? Map<String, Any> ?: wrongType(key)

    private fun asList(value: Any, key: String): List<Any> =
        (value as? List<*>)?.map { it ?: wrongType(key) } ?: wrongType(key)

    private fun wrongType(key: String): Nothing = throw IllegalArgumentException("wrong_type: $key")
}
