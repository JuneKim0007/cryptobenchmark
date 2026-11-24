package io.github.junekim0007.cryptobench.document.names

import io.github.junekim0007.cryptobench.document.names.dto.Canonical

/** The capture's provider aliases over the names file, as Python's shared/catalogue/name_layers merges them; a conflict's text names every row, in any row order. */
object NameLayers {

    fun merged(base: AlgorithmNames, capture: CaptureSpellings?): AlgorithmNames {
        if (capture == null) return base
        val added = linkedMapOf<Pair<String, String>, Canonical>()
        val said = hashMapOf<Pair<String, String>, MutableSet<String>>()
        val split = linkedMapOf<Pair<String, String>, String?>()
        for ((provider, services) in capture.services) {
            for (service in services) {
                val target = base.catalogued(service.type, service.name)
                for (alias in service.aliases) {
                    val at = service.type to AlgorithmNames.fold(alias)
                    val static = base.catalogued(service.type, alias)
                    said.getOrPut(at) { HashSet() }.add("$provider says ${target.name}")
                    if (static.known && static.key != target.key) {
                        split[at] = "catalog says ${static.name}; "
                    } else if (!static.known && added.getOrPut(at) { target }.key != target.key) {
                        split[at] = ""
                    }
                }
            }
        }
        return base.layered(added, split.mapValues { (at, prefix) -> prefix + said.getValue(at).sorted().joinToString(", ") })
    }
}
