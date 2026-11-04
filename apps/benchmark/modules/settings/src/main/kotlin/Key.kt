package io.github.junekim0007.cryptobench.settings

/** One YAML setting of a section: a Leaf holds one value, a Nested holds another section. */
sealed class Key<O, T : Any>(val name: String, private val get: (O) -> T?, private val with: (O, T?) -> O) {

    abstract fun read(value: Any, label: String, path: String): T
    abstract fun write(value: T): Any
    abstract fun merge(base: T, later: T): T
    abstract fun unsupported(value: T, facts: Facts, path: String): List<Unsupported>
    abstract fun honoured(value: T, unsupported: List<Unsupported>, facts: Facts, path: String): T?

    fun readInto(target: O, value: Any, label: String, path: String): O = with(target, read(value, label, path))

    fun writeFrom(source: O, into: MutableMap<String, Any>) {
        get(source)?.let { into[name] = write(it) }
    }

    fun mergeInto(base: O, later: O): O {
        val next = get(later) ?: return base
        return with(base, get(base)?.let { merge(it, next) } ?: next)
    }

    fun unsupportedIn(source: O, facts: Facts, path: String): List<Unsupported> =
        get(source)?.let { unsupported(it, facts, "$path.$name") }.orEmpty()

    fun honouredIn(source: O, unsupported: List<Unsupported>, facts: Facts, path: String): O =
        get(source)?.let { with(source, honoured(it, unsupported, facts, "$path.$name")) } ?: source
}

class Leaf<O, T : Any>(
    name: String,
    private val reader: (Any, String) -> T,
    get: (O) -> T?,
    with: (O, T?) -> O,
    private val writer: (T) -> Any = { it },
) : Key<O, T>(name, get, with) {
    override fun read(value: Any, label: String, path: String): T = reader(value, label)
    override fun write(value: T): Any = writer(value)
    override fun merge(base: T, later: T): T = later
    override fun unsupported(value: T, facts: Facts, path: String): List<Unsupported> = emptyList()
    override fun honoured(value: T, unsupported: List<Unsupported>, facts: Facts, path: String): T? =
        value.takeUnless { unsupported.any { it.path == path } }
}

/** A block merged key by key; requires decides the whole block, resolve fits a supported block to the device. */
class Nested<O, C : Any>(
    name: String,
    private val section: Section<C>,
    get: (O) -> C?,
    with: (O, C?) -> O,
    private val requires: (C, Facts) -> Support = { _, _ -> Support.Supported },
    private val resolve: (C, Facts) -> C = { value, _ -> value },
) : Key<O, C>(name, get, with) {
    override fun read(value: Any, label: String, path: String): C = section.read(Values.section(value, path), path)
    override fun write(value: C): Any = section.write(value)
    override fun merge(base: C, later: C): C = section.merged(base, later)
    override fun unsupported(value: C, facts: Facts, path: String): List<Unsupported> = when (val support = requires(value, facts)) {
        Support.Supported -> section.unsupported(value, facts, path)
        is Support.NotSupported -> listOf(Unsupported(path, support.reason, support.required))
    }
    override fun honoured(value: C, unsupported: List<Unsupported>, facts: Facts, path: String): C? =
        if (unsupported.any { it.path == path }) null else resolve(section.honoured(value, unsupported, facts, path), facts)
}
