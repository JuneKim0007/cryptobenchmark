package io.github.junekim0007.cryptobench.settings

/** An ordered table of keys: reading rejects unknown keys, writing emits only what is set, merging is key by key. */
class Section<O>(private val empty: O, private val prefix: String, private val keys: () -> List<Key<O, *>>) {

    val names: List<String> get() = keys().map { it.name }

    fun read(document: Map<String, Any>?, path: String): O {
        if (document == null) return empty
        val unknown = document.keys.filter { it !in names }
        require(unknown.isEmpty()) { "unknown_keys: $path $unknown, known $names" }
        return keys().fold(empty) { built, key ->
            val value = document[key.name] ?: return@fold built
            if (key.nested) key.readInto(built, value, prefix + key.name, "$path.${key.name}")
            else try {
                key.readInto(built, value, prefix + key.name, path)
            } catch (failure: IllegalArgumentException) {
                throw IllegalArgumentException("${failure.message} at $path", failure)
            }
        }
    }

    fun write(value: O): Map<String, Any> = LinkedHashMap<String, Any>().also { out -> keys().forEach { it.writeFrom(value, out) } }

    fun merged(base: O, later: O?): O = if (later == null) base else keys().fold(base) { merged, key -> key.mergeInto(merged, later) }
}
