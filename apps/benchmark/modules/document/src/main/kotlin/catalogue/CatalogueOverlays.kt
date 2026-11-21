package io.github.junekim0007.cryptobench.document.catalogue

import io.github.junekim0007.cryptobench.document.DocumentFields
import io.github.junekim0007.cryptobench.document.YamlCodec

/** algorithms/provider-builds.yaml and deviations.yaml: per build, what a provider-wide behaviour or a deviation states of one entry, and the build a provider runs as here. */
class CatalogueOverlays(private val builds: Map<String, String>, private val behaviours: List<Statement>, private val deviations: List<Statement>) {

    class Statement(val builds: List<String>, val ids: Set<String>, val set: Map<String, Any?>)

    // as the guide's reader: a behaviour (its names exact) only where the entry has the field's parent, then each deviation (names folded) in file order
    fun stated(id: String, entry: Map<String, Any?>): Map<String, Map<String, Any?>> {
        val found = linkedMapOf<String, MutableMap<String, Any?>>()
        for (behaviour in behaviours.filter { id in it.ids }) {
            behaviour.builds.forEach { found.getOrPut(it) { linkedMapOf() }.putAll(behaviour.set.filterKeys { path -> Overrides.parent(entry, path) != null }) }
        }
        for (deviation in deviations.filter { FamilyCatalogue.fold(id) in it.ids }) {
            deviation.builds.forEach { found.getOrPut(it) { linkedMapOf() }.putAll(deviation.set) }
        }
        return found
    }

    /** The provider's build on this platform (android-<sdk>, jdk-<major>): exact, else the nearest at or below of its kind, else its latest; null when none is measured. */
    fun build(provider: String, platform: String?): String? {
        val keys = builds.filterValues { it == provider }.keys.sorted()
        if ("$provider @ $platform" in keys) return "$provider @ $platform"
        val kind = platform?.let { PLATFORM.matchEntire(it) }
        val sameKind = kind?.let { match -> keys.mapNotNull { key -> Regex(" @ ${match.groupValues[1]}-(\\d+)$").find(key)?.let { it.groupValues[1].toInt() to key } } }
            .orEmpty().sortedWith(compareBy({ it.first }, { it.second }))
        if (sameKind.isNotEmpty()) return (sameKind.lastOrNull { it.first <= kind!!.groupValues[2].toInt() } ?: sameKind.first()).second
        return keys.lastOrNull()
    }

    companion object {

        val NONE = CatalogueOverlays(emptyMap(), emptyList(), emptyList())
        private val PLATFORM = Regex("(\\w+)-(\\d+)")

        /** The platform [build] takes: android-<sdk> where an API level is captured, else jdk-<major>; null when neither is. */
        fun platform(sdkInt: Int?, javaVersion: String?): String? =
            sdkInt?.takeIf { it > 0 }?.let { "android-$it" } ?: javaVersion?.substringBefore('.')?.takeIf { it.isNotEmpty() }?.let { "jdk-$it" }

        fun parse(providerBuilds: String, deviations: String): CatalogueOverlays {
            val document = YamlCodec.DOCUMENT.load(providerBuilds)
            val builds = DocumentFields.section(document, "builds").mapValues { (key, row) -> DocumentFields.string(DocumentFields.asSection(row, key), "name") }
            fun expanded(words: List<String>) = words.flatMap { word ->
                if (word in builds) listOf(word) else builds.filterValues { it == word }.keys.sorted().ifEmpty { throw IllegalStateException("provider_build_unknown: '$word' is no build or provider") }
            }
            val behaviours = DocumentFields.sectionOrEmpty(document, "providers").flatMap { (name, value) ->
                val provider = DocumentFields.asSection(value, name)
                val behaviour = DocumentFields.sectionOrEmpty(provider, "behaviour")
                DocumentFields.sections(provider, "registers").map { Statement(expanded(DocumentFields.strings(it, "builds")), DocumentFields.strings(it, "names").toSet(), behaviour) }
            }
            val stated = DocumentFields.section(YamlCodec.DOCUMENT.load(deviations), "deviations").map { (key, value) ->
                val row = DocumentFields.asSection(value, key)
                Statement(expanded(DocumentFields.strings(row, "builds")), DocumentFields.strings(row, "names").mapTo(HashSet(), FamilyCatalogue::fold), DocumentFields.section(row, "set"))
            }
            return CatalogueOverlays(builds, behaviours, stated)
        }
    }
}
