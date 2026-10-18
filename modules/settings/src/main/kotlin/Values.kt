package io.github.junekim0007.cryptobench.settings

/** Typed reads of one YAML value; the message names the key, the section appends where. */
object Values {

    fun int(min: Int, code: String, hint: String = ""): (Any, String) -> Int = { value, label ->
        val number = (value as? Number)?.toInt() ?: throw IllegalArgumentException("wrong_type: $label expects a number, got ${value::class.simpleName}")
        require(number >= min) { "$code: $label $number$hint" }
        number
    }

    fun choice(known: List<String>): (Any, String) -> String = { value, label ->
        if (value is Boolean) throw IllegalArgumentException("invalid: $label $value (YAML reads off/on/yes/no as booleans), write one of $known")
        val text = value as? String ?: throw IllegalArgumentException("wrong_type: $label expects text, got ${value::class.simpleName}")
        require(text in known) { "invalid: $label $text, known $known" }
        text
    }

    fun section(value: Any, path: String): Map<String, Any> {
        @Suppress("UNCHECKED_CAST")
        return value as? Map<String, Any> ?: throw IllegalArgumentException("wrong_type: $path expects a mapping, got ${value::class.simpleName}")
    }
}
