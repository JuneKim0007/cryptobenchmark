package io.github.junekim0007.cryptobench.config.yaml

object DocumentFields {

    fun string(document: Map<String, Any>, key: String): String =
        field(document, key) as? String ?: wrongType(key)

    fun number(document: Map<String, Any>, key: String): Number =
        field(document, key) as? Number ?: wrongType(key)

    fun boolean(document: Map<String, Any>, key: String): Boolean =
        field(document, key) as? Boolean ?: wrongType(key)

    fun section(document: Map<String, Any>, key: String): Map<String, Any> =
        asSection(field(document, key), key)

    fun sections(document: Map<String, Any>, key: String): List<Map<String, Any>> =
        asList(field(document, key), key).map { asSection(it, key) }

    fun strings(document: Map<String, Any>, key: String): List<String> =
        asList(field(document, key), key).map { it as? String ?: wrongType(key) }

    fun numbers(document: Map<String, Any>, key: String): List<Int> =
        asList(field(document, key), key).map { (it as? Number ?: wrongType(key)).toInt() }

    inline fun <T> optional(document: Map<String, Any>, key: String, default: T, read: (Map<String, Any>, String) -> T): T =
        if (document[key] == null) default else read(document, key)

    fun optionalString(document: Map<String, Any>, key: String): String = optional(document, key, "", ::string)

    fun optionalStringOrNull(document: Map<String, Any>, key: String): String? = optional(document, key, null, ::string)

    fun optionalNumber(document: Map<String, Any>, key: String): Number? = optional(document, key, null, ::number)

    fun optionalBoolean(document: Map<String, Any>, key: String): Boolean = optional(document, key, false, ::boolean)

    fun optionalSection(document: Map<String, Any>, key: String): Map<String, Any>? = optional(document, key, null, ::section)

    fun optionalSections(document: Map<String, Any>, key: String): List<Map<String, Any>> = optional(document, key, emptyList(), ::sections)

    fun optionalStrings(document: Map<String, Any>, key: String): List<String> = optional(document, key, emptyList(), ::strings)

    fun optionalNumbers(document: Map<String, Any>, key: String): List<Int> = optional(document, key, emptyList(), ::numbers)

    fun optionalNumbersOrNull(document: Map<String, Any>, key: String): List<Int>? = optional(document, key, null, ::numbers)

    fun expectKeys(document: Map<String, Any>, allowed: Collection<String>, path: String) {
        val unknown = document.keys.filter { it !in allowed }
        if (unknown.isNotEmpty()) throw IllegalArgumentException("unknown_keys: $path $unknown, known $allowed")
    }

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
