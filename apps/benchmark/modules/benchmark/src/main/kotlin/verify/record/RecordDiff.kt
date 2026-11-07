package io.github.junekim0007.cryptobench.benchmark.verify.record

/** Two check.yaml case lists: every case only in one, and every field path whose value differs, one line each. */
object RecordDiff {

    fun of(baseline: List<Map<String, Any>>, current: List<Map<String, Any>>): List<String> {
        val before = byId(baseline)
        val after = byId(current)
        val lines = mutableListOf<String>()
        before.keys.filterNot { it in after }.forEach { lines += "removed: $it" }
        after.keys.filterNot { it in before }.forEach { lines += "added: $it" }
        for (id in before.keys.filter { it in after }) {
            val a = flat(before.getValue(id))
            val b = flat(after.getValue(id))
            for (path in (a.keys + b.keys).distinct()) {
                if (a[path] != b[path]) lines += "changed: $id: $path: ${a[path] ?: "absent"} -> ${b[path] ?: "absent"}"
            }
        }
        return lines
    }

    private fun byId(cases: List<Map<String, Any>>): Map<String, Map<String, Any>> =
        cases.associateBy { it["id"].toString() }.also { require(it.size == cases.size) { "duplicate_id: a check.yaml repeats a case id" } }

    private fun flat(value: Any?, prefix: String = ""): Map<String, String> = when (value) {
        is Map<*, *> -> value.entries.fold(LinkedHashMap()) { all, (key, inner) -> all.apply { putAll(flat(inner, if (prefix.isEmpty()) "$key" else "$prefix.$key")) } }
        else -> mapOf(prefix to value.toString())
    }
}
