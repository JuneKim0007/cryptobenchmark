package io.github.junekim0007.cryptobench.settings

/** One YAML setting: how it is read, written, merged, and read back off the typed value it belongs to. */
class Key<O, T : Any>(
    val name: String,
    private val read: (Any, String, String) -> T,
    private val get: (O) -> T?,
    private val with: (O, T) -> O,
    private val write: (T) -> Any = { it },
    private val merge: (T, T) -> T = { _, later -> later },
    val nested: Boolean = false,
) {
    fun readInto(target: O, value: Any, label: String, path: String): O = with(target, read(value, label, path))

    fun writeFrom(source: O, into: MutableMap<String, Any>) {
        get(source)?.let { into[name] = write(it) }
    }

    fun mergeInto(base: O, later: O): O {
        val next = get(later) ?: return base
        val current = get(base)
        return with(base, if (current == null) next else merge(current, next))
    }

    companion object {
        fun <O, T : Any> value(name: String, read: (Any, String) -> T, get: (O) -> T?, with: (O, T) -> O): Key<O, T> =
            Key(name, { value, label, _ -> read(value, label) }, get, with)

        fun <O, C : Any> section(name: String, section: Section<C>, get: (O) -> C?, with: (O, C) -> O): Key<O, C> =
            Key(name, { value, _, path -> section.read(Values.section(value, path), path) }, get, with,
                write = { section.write(it) }, merge = { base, later -> section.merged(base, later) }, nested = true)
    }
}
