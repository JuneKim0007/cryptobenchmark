package io.github.junekim0007.cryptobench.config.layers

import io.github.junekim0007.cryptobench.document.SchemaVersion
import io.github.junekim0007.cryptobench.config.global.GlobalDocument
import io.github.junekim0007.cryptobench.document.YamlCodec
import io.github.junekim0007.cryptobench.document.versioned.DocumentReader
import io.github.junekim0007.cryptobench.document.versioned.YamlFiles
import io.github.junekim0007.cryptobench.files.Beside
import org.yaml.snakeyaml.error.YAMLException
import java.io.File
import java.security.MessageDigest

/** A composition's layers, lowest first, then its own keys, merged by MERGE_RULES; a file without layers: is a stack of one. */
object LayerStack {

    const val LAYERS = "layers"

    enum class Merge { BY_KEY, REPLACE }

    // a mapping not named here merges by key; lists and scalars always replace
    val MERGE_RULES: Map<String, Merge> = mapOf("run.passes" to Merge.REPLACE)

    data class Layer(val path: String, val sha256: String)

    /** sources: each dotted leaf the layers wrote, to the 1-based layer it came from. */
    data class Merged(val document: Map<String, Any>, val layers: List<Layer>, val sources: Map<String, Int>) {
        fun named(index: Int): String = "layer $index ${layers[index - 1].path}"
    }

    fun read(file: File): Merged {
        val (own, names) = YamlFiles().readOnly(file, Composition).read()
        if (names == null) return merged(listOf(Layer(file.name, sha256(file)) to own - SchemaVersion.FIELD))
        val layers = names.map { name ->
            val layerFile = Beside.authored(file, name)
            require(layerFile.isFile) { "missing_file: ${layerFile.path} (${file.name} $LAYERS)" }
            val layer = load(layerFile, name)
            require(LAYERS !in layer) { "nested_layers: $name lists $LAYERS; only the composition ${file.name} lists layers" }
            if (SchemaVersion.FIELD in layer) SchemaVersion.require(layer, GlobalDocument.schemaVersion, name)
            Layer(name, sha256(layerFile)) to layer - SchemaVersion.FIELD
        }
        return merged(layers + (Layer(file.name, sha256(file)) to own - SchemaVersion.FIELD - LAYERS))
    }

    // the composition's own keys and the layers it lists, null without layers:
    private object Composition : DocumentReader<Pair<Map<String, Any>, List<String>?>> {

        override val schemaVersion = GlobalDocument.schemaVersion

        override fun parse(document: Map<String, Any>): Pair<Map<String, Any>, List<String>?> {
            val listed = document[LAYERS] ?: return document to null
            val names = (listed as? List<*>)?.map { it as? String ?: throw IllegalArgumentException("wrong_type: $LAYERS, expected a list of paths") }
                ?: throw IllegalArgumentException("wrong_type: $LAYERS, expected a list of paths")
            require(names.isNotEmpty()) { "empty: $LAYERS" }
            return document to names
        }
    }

    private fun merged(layers: List<Pair<Layer, Map<String, Any>>>): Merged {
        val document = LinkedHashMap<String, Any>()
        val sources = LinkedHashMap<String, Int>()
        layers.forEachIndexed { at, (_, values) -> merge(document, values, "", at + 1, sources) }
        return Merged(document, layers.map { it.first }, sources)
    }

    @Suppress("UNCHECKED_CAST")
    private fun merge(into: MutableMap<String, Any>, layer: Map<String, Any>, prefix: String, index: Int, sources: MutableMap<String, Int>) {
        for ((key, value) in layer) {
            val path = prefix + key
            val earlier = into[key]
            if (value is Map<*, *> && earlier is Map<*, *> && MERGE_RULES[path] != Merge.REPLACE) {
                val nested = LinkedHashMap(earlier as Map<String, Any>)
                merge(nested, value as Map<String, Any>, "$path.", index, sources)
                into[key] = nested
                continue
            }
            sources.keys.removeAll { it == path || it.startsWith("$path.") }
            into[key] = value
            leaves(value, path).forEach { sources[it] = index }
        }
    }

    private fun leaves(value: Any, path: String): List<String> =
        if (value is Map<*, *> && value.isNotEmpty()) value.entries.flatMap { (key, inner) -> leaves(inner ?: "", "$path.$key") } else listOf(path)

    // a layer's schemaVersion is optional and its refusals name its path as listed, so it skips VersionedFile
    private fun load(file: File, name: String): Map<String, Any> = try {
        YamlCodec.DOCUMENT.load(file.readText())
    } catch (failure: YAMLException) {
        throw IllegalArgumentException("unreadable_yaml: $name: ${failure.message}", failure)
    }

    private fun sha256(file: File): String = MessageDigest.getInstance("SHA-256").digest(file.readBytes()).joinToString("") { "%02x".format(it) }
}
