package io.github.junekim0007.cryptobench.document.catalogue

/** A build's `<path>: <value>` on a copy of an entry: a field by its dotted path, or a whole required or optional row by name, which null drops. */
internal object Overrides {

    private val ROWS = setOf("required", "optional")

    // the mapping holding the path's last step; a list step picks the item of that name or fact
    fun parent(entry: Map<String, Any?>, path: String): MutableMap<String, Any?>? {
        val steps = path.split('.')
        if (steps.size < 2 || steps.last().isEmpty() || steps.first() == FamilyCatalogue.PROVIDERS) return null
        var node: Any? = entry
        for (step in steps.dropLast(1)) {
            node = when (node) {
                is Map<*, *> -> node[step]
                is List<*> -> node.firstOrNull { it is Map<*, *> && (it["name"] == step || it["fact"] == step) }
                else -> null
            }
        }
        @Suppress("UNCHECKED_CAST")
        return node as? MutableMap<String, Any?>
    }

    fun apply(view: MutableMap<String, Any?>, path: String, value: Any?) {
        val steps = path.split('.')
        if (steps.size == 2 && steps[0] in ROWS) {
            val kept = (view[steps[0]] as? List<*>).orEmpty().filterNot { it is Map<*, *> && it["name"] == steps[1] }
            view[steps[0]] = if (value == null) kept else kept + copy(value)
            return
        }
        parent(view, path)?.put(steps.last(), copy(value))
    }

    fun copy(value: Any?): Any? = when (value) {
        is Map<*, *> -> LinkedHashMap<String, Any?>().apply { value.forEach { (k, v) -> put(k as String, copy(v)) } }
        is List<*> -> value.mapTo(ArrayList()) { copy(it) }
        else -> value
    }
}
