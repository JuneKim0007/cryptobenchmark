package io.github.junekim0007.cryptobench.settings

/** Type checks for one YAML value; bounds and choices are checked by the class the value goes into. */
object Values {

    val int: (Any, String) -> Int = { value, label -> (value as? Number)?.toInt() ?: throw wrongType(label, "a number", value) }

    val boolean: (Any, String) -> Boolean = { value, label -> value as? Boolean ?: throw wrongType(label, "true or false", value) }

    fun text(known: List<String>): (Any, String) -> String = { value, label ->
        if (value is Boolean) throw IllegalArgumentException("invalid: $label $value (YAML reads off/on/yes/no as booleans), write one of $known")
        value as? String ?: throw wrongType(label, "text", value)
    }

    fun section(value: Any, path: String): Map<String, Any> {
        @Suppress("UNCHECKED_CAST")
        return value as? Map<String, Any> ?: throw IllegalArgumentException("wrong_type: $path expects a mapping, got ${value::class.simpleName}")
    }

    internal fun wrongType(label: String, expected: String, value: Any) =
        IllegalArgumentException("wrong_type: $label expects $expected, got ${value::class.simpleName}")
}
