package io.github.junekim0007.cryptobench.config.layers

/** generatedFrom.settings: each value written, to the layer that set it or "default"; what the layers set that is not written stays listed. */
object Provenance {

    const val DEFAULT = "default"

    /** inherited: a written block to the block its unset leaves came from, labelled with that leaf's source "via" it. */
    fun settings(written: Map<String, Any>, stack: LayerStack.Merged, inherited: Map<String, String> = emptyMap()): Map<String, String> {
        val settings = LinkedHashMap<String, String>()
        for (path in leaves(written, "")) {
            settings[path] = source(path, stack) ?: inherited.entries.firstOrNull { path.startsWith("${it.key}.") }
                ?.let { (block, from) -> source(from + path.removePrefix(block), stack)?.let { "$it via $from" } } ?: DEFAULT
        }
        stack.sources.filterKeys { source -> settings.keys.none { it == source || it.startsWith("$source.") || source.startsWith("$it.") } }
            .forEach { (source, index) -> settings[source] = stack.named(index) }
        return settings
    }

    /** The message of a failed parse with the layer that wrote the key it names. */
    fun located(message: String, stack: LayerStack.Merged): String {
        val named = message.substringBefore(", known")
        val source = stack.sources.entries.firstOrNull { (path, _) -> path.split('.').any { Regex("[\\[ ]${Regex.escape(it)}[,\\]]").containsMatchIn(named) } }
        return source?.let { "$message (${stack.named(it.value)})" } ?: message
    }

    private fun source(path: String, stack: LayerStack.Merged): String? =
        stack.sources.entries.firstOrNull { (source, _) -> path == source || path.startsWith("$source.") || source.startsWith("$path.") }?.let { stack.named(it.value) }

    private fun leaves(value: Any?, prefix: String): List<String> =
        if (value is Map<*, *> && value.isNotEmpty()) value.entries.flatMap { (key, inner) -> leaves(inner, if (prefix.isEmpty()) "$key" else "$prefix.$key") }
        else listOf(prefix)
}
