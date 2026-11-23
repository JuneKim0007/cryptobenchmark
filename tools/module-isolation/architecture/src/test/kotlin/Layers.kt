package io.github.junekim0007.cryptobench.architecture

import org.yaml.snakeyaml.Yaml
import java.io.File

data class Forbidden(val module: String, val from: String, val to: String) {
    fun covers(className: String): Boolean = className.startsWith("$module.$from.")

    fun targets(className: String): Boolean =
        if (to.substringAfterLast('.').first().isUpperCase()) className == "$module.$to" else className.startsWith("$module.$to.")
}

class Layers(
    val root: String,
    val uses: Map<String, Map<String, Set<String>?>>,
    val cycles: List<String>,
    val forbidden: List<Forbidden>,
    val consumers: Map<String, Map<String, Set<String>?>>,
) {
    fun moduleOf(className: String): String? = className.substringBefore('.').takeIf { it in uses && '.' in className }

    fun staleEntries(classNames: Set<String>): List<String> =
        (uses + consumers).flatMap { (user, lists) ->
            lists.flatMap { (module, names) -> names.orEmpty().filter { "$module.$it" !in classNames }.map { "stale_entry: $user uses $module.$it: no such class in $module" } }
        }

    companion object {
        @Suppress("UNCHECKED_CAST")
        fun read(file: File): Layers {
            val doc = Yaml().load<Map<String, Any>>(file.readText())
            val modules = doc.getValue("modules") as Map<String, Map<String, Any>>
            val lists: (Map<String, Any>) -> Map<String, Set<String>?> = { m ->
                (m["uses"] as Map<String, Any>).mapValues { (_, names) -> if (names == "all") null else (names as List<String>).toSet() }
            }
            val uses = modules.mapValues { (_, m) -> lists(m) }
            val consumers = (doc.getValue("consumers") as Map<String, Map<String, Any>>).mapValues { (_, c) -> lists(c) }
            val forbidden = (doc["forbidden"] as List<Map<String, String>>).map { Forbidden(it.getValue("module"), it.getValue("from"), it.getValue("to")) }
            return Layers(doc.getValue("root") as String, uses, doc.getValue("cycles") as List<String>, forbidden, consumers)
        }
    }
}
