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
            if (key is Nested<*, *>) key.readInto(built, value, prefix + key.name, "$path.${key.name}")
            else try {
                key.readInto(built, value, prefix + key.name, path)
            } catch (failure: IllegalArgumentException) {
                throw IllegalArgumentException("${failure.message} at $path", failure)
            }
        }
    }

    fun write(value: O): Map<String, Any> = LinkedHashMap<String, Any>().also { out -> keys().forEach { it.writeFrom(value, out) } }

    fun merged(base: O, later: O?): O = if (later == null) base else keys().fold(base) { merged, key -> key.mergeInto(merged, later) }

    fun unsupported(value: O, facts: Facts, path: String): List<Unsupported> = keys().flatMap { it.unsupportedIn(value, facts, path) }

    fun honoured(value: O, unsupported: List<Unsupported>, facts: Facts, path: String): O =
        keys().fold(value) { kept, key -> key.honouredIn(kept, unsupported, facts, path) }

    /** What this device can run, and what it cannot, in one pass. */
    fun forDevice(value: O, facts: Facts, path: String): Pair<O, List<Unsupported>> {
        val unsupported = unsupported(value, facts, path)
        return honoured(value, unsupported, facts, path) to unsupported
    }
}
