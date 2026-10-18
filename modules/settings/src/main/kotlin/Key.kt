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
    private val requires: (T, Facts) -> Support = { _, _ -> Support.Supported },
    private val drop: (O) -> O = { it },
    private val children: ((T, Facts, String) -> List<Unsupported>)? = null,
    private val prune: ((T, List<Unsupported>, String) -> T)? = null,
    private val required: (T) -> Boolean = { false },
) {
    fun readInto(target: O, value: Any, label: String, path: String): O = with(target, read(value, label, path))

    fun writeFrom(source: O, into: MutableMap<String, Any>) {
        get(source)?.let { into[name] = write(it) }
    }

    /** Set and unsupported on this device; a nested key reports its own keys instead of itself. */
    fun unsupported(source: O, facts: Facts, path: String): List<Unsupported> {
        val value = get(source) ?: return emptyList()
        children?.let { return it(value, facts, "$path.$name") }
        return when (val support = requires(value, facts)) {
            Support.Supported -> emptyList()
            is Support.NotSupported -> listOf(Unsupported("$path.$name", support.reason, required(value)))
        }
    }

    /** The source with this key removed when it is unsupported, or, for a nested key, with its unsupported keys removed. */
    fun supportedIn(source: O, unsupported: List<Unsupported>, path: String): O {
        val value = get(source) ?: return source
        prune?.let { return with(source, it(value, unsupported, "$path.$name")) }
        return if (unsupported.any { it.path == "$path.$name" }) drop(source) else source
    }

    fun mergeInto(base: O, later: O): O {
        val next = get(later) ?: return base
        val current = get(base)
        return with(base, if (current == null) next else merge(current, next))
    }

    companion object {
        fun <O, T : Any> value(
            name: String, read: (Any, String) -> T, get: (O) -> T?, with: (O, T) -> O,
            drop: (O) -> O = { it }, requires: (T, Facts) -> Support = { _, _ -> Support.Supported },
        ): Key<O, T> = Key(name, { value, label, _ -> read(value, label) }, get, with, requires = requires, drop = drop)

        fun <O, C : Any> section(name: String, section: Section<C>, get: (O) -> C?, with: (O, C) -> O): Key<O, C> =
            Key(name, { value, _, path -> section.read(Values.section(value, path), path) }, get, with,
                write = { section.write(it) }, merge = { base, later -> section.merged(base, later) }, nested = true,
                children = { value, facts, path -> section.unsupported(value, facts, path) },
                prune = { value, unsupported, path -> section.supported(value, unsupported, path) })
    }
}
