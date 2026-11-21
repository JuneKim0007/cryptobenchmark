package io.github.junekim0007.cryptobench.files

import java.io.File

/** The .json a contract fixture states for a YAML value, in the bytes Python's json.dumps(value, indent=1) writes. */
object StatedJson {

    fun write(file: File, value: Any?) = file.writeText(text(value, 0) + "\n")

    private fun text(value: Any?, depth: Int): String = when (value) {
        null -> "null"
        is Boolean, is Int, is Long, is java.math.BigInteger -> value.toString()
        is Double -> value.toString().also { require('E' !in it && it.toDouble().isFinite()) { "no_json_form: $it" } }
        is String -> quoted(value)
        is Map<*, *> -> block(value.entries.map { (key, item) -> "${quoted(key as String)}: ${text(item, depth + 1)}" }, depth, "{", "}")
        is List<*> -> block(value.map { text(it, depth + 1) }, depth, "[", "]")
        else -> throw IllegalArgumentException("no_json_form: ${value::class.java.name}")
    }

    private fun block(items: List<String>, depth: Int, open: String, close: String): String {
        if (items.isEmpty()) return open + close
        val inner = " ".repeat(depth + 1)
        return items.joinToString(",\n", "$open\n", "\n${" ".repeat(depth)}$close") { inner + it }
    }

    // ensure_ascii: every character outside space..~ is escaped
    private fun quoted(text: String): String = buildString {
        append('"')
        for (c in text) when (c) {
            '"' -> append("\\\"")
            '\\' -> append("\\\\")
            '\n' -> append("\\n")
            '\r' -> append("\\r")
            '\t' -> append("\\t")
            '\b' -> append("\\b")
            '\u000c' -> append("\\f")
            in ' '..'~' -> append(c)
            else -> append("\\u%04x".format(c.code))
        }
        append('"')
    }
}
