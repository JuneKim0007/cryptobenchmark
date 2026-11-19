package io.github.junekim0007.cryptobench.document

/** A double-quoted YAML scalar for files written one line at a time. */
object YamlLine {
    fun quoted(text: String): String = "\"" + text.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n") + "\""
}
