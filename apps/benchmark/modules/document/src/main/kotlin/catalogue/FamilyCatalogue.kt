package io.github.junekim0007.cryptobench.document.catalogue

import io.github.junekim0007.cryptobench.document.DocumentFields
import io.github.junekim0007.cryptobench.document.YamlCodec
import java.util.Locale

/** algorithms/<family>_catalogue.yaml read whole: each entry by type and name, its fields as one provider build runs it, the entry's own providers section over [CatalogueOverlays] as the guide's reader applies them. */
class FamilyCatalogue(val entries: List<Entry>, private val overlays: CatalogueOverlays = CatalogueOverlays.NONE) {

    class Entry(val family: String, val type: String, val name: String, private val fields: Map<String, Any?>, private val builds: Map<String, Map<String, Any?>>) {

        val id: String get() = "$type|$name"

        fun fields(build: String? = null): Map<String, Any?> {
            val differences = builds[build] ?: return fields
            @Suppress("UNCHECKED_CAST")
            val view = Overrides.copy(fields) as MutableMap<String, Any?>
            differences.forEach { (path, value) -> Overrides.apply(view, path, value) }
            return view
        }

        @Suppress("UNCHECKED_CAST")
        fun section(key: String, build: String? = null): Map<String, Any?>? = fields(build)[key] as? Map<String, Any?>
    }

    private val byId = entries.associateBy { fold(it.id) }

    fun of(type: String, name: String): Entry? = byId[fold("$type|$name")]

    /** The build a provider runs as on this platform, whose view [Entry.fields] gives; null: the base entry. */
    fun build(provider: String, platform: String?): String? = overlays.build(provider, platform)

    companion object {

        internal const val PROVIDERS = "providers"
        const val PROVIDER_BUILDS = "provider-builds.yaml"
        const val DEVIATIONS = "deviations.yaml"

        fun fold(name: String): String = name.uppercase(Locale.ROOT)

        fun file(family: String) = "${family}_catalogue.yaml"

        /** A guide file carried beside this class. */
        fun resource(name: String): String =
            FamilyCatalogue::class.java.getResource(name)?.readText() ?: throw IllegalStateException("missing_resource: $name is not beside ${FamilyCatalogue::class.java.name}")

        fun bundled(families: List<String>): FamilyCatalogue =
            parse(families.map { resource(file(it)) }, CatalogueOverlays.parse(resource(PROVIDER_BUILDS), resource(DEVIATIONS)))

        fun parse(texts: List<String>, overlays: CatalogueOverlays = CatalogueOverlays.NONE): FamilyCatalogue = FamilyCatalogue(texts.flatMap { text ->
            val document = YamlCodec.DOCUMENT.load(text)
            val family = DocumentFields.optionalString(document, "family")
            DocumentFields.section(document, "algorithms").map { (id, value) ->
                @Suppress("UNCHECKED_CAST")
                val raw = DocumentFields.asSection(value, id) as Map<String, Any?>
                Entry(family, id.substringBefore('|'), id.substringAfter('|'), raw.filterKeys { it != PROVIDERS }, builds(id, raw, overlays))
            }
        }, overlays)

        // as the guide's reader: only an entry with a providers section takes the overlays; its own fields win per build
        private fun builds(id: String, raw: Map<String, Any?>, overlays: CatalogueOverlays): Map<String, Map<String, Any?>> {
            val own = raw[PROVIDERS] as? Map<*, *> ?: return emptyMap()
            val merged = overlays.stated(id, raw).mapValuesTo(LinkedHashMap()) { LinkedHashMap(it.value) }
            own.forEach { (build, fields) -> (fields as? Map<*, *>)?.forEach { (path, v) -> merged.getOrPut(build as String) { linkedMapOf() }[path as String] = v } }
            return merged
        }
    }
}
