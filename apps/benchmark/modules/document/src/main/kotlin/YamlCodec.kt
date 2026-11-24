package io.github.junekim0007.cryptobench.document

import java.io.Writer
import org.yaml.snakeyaml.DumperOptions
import org.yaml.snakeyaml.LoaderOptions
import org.yaml.snakeyaml.Yaml
import org.yaml.snakeyaml.constructor.Constructor
import org.yaml.snakeyaml.constructor.SafeConstructor
import org.yaml.snakeyaml.representer.Representer

private fun loaderOptions(): LoaderOptions = LoaderOptions().apply { codePointLimit = YamlCodec.CODE_POINT_LIMIT }

/** The one SnakeYAML setup, by profile; a profile's bytes and load failures are part of what its files promise. */
enum class YamlCodec {

    // config, preparation and benchmark's YAML files: flow style AUTO, aliases dereferenced, safe constructor, duplicate keys and non-mappings refused
    DOCUMENT {
        override fun yaml(): Yaml {
            val dumperOptions = DumperOptions().apply {
                defaultFlowStyle = DumperOptions.FlowStyle.AUTO
                indent = 2
                isDereferenceAliases = true
            }
            val loaderOptions = loaderOptions().apply { isAllowDuplicateKeys = false }
            return Yaml(SafeConstructor(loaderOptions), Representer(dumperOptions), dumperOptions, loaderOptions)
        }

        @Suppress("UNCHECKED_CAST")
        override fun mapping(loaded: Any?): Map<String, Any> =
            loaded as? Map<String, Any> ?: throw IllegalArgumentException("not_a_mapping: the document is not a set of key: value entries")
    },

    // discovery: block style, aliases kept, SnakeYAML's default constructor (duplicate keys: last wins)
    CAPTURE {
        override fun yaml(): Yaml {
            val dumperOptions = DumperOptions().apply {
                defaultFlowStyle = DumperOptions.FlowStyle.BLOCK
                indent = 2
            }
            val loaderOptions = loaderOptions()
            return Yaml(Constructor(loaderOptions), Representer(dumperOptions), dumperOptions, loaderOptions)
        }

        // unchecked: an empty document throws NullPointerException, a list ClassCastException
        @Suppress("UNCHECKED_CAST")
        override fun mapping(loaded: Any?): Map<String, Any> = loaded as Map<String, Any>
    },

    // benchmark's result inputs (androidx JSON, energy, passes): safe constructor, duplicate keys last-wins; read only
    RESULTS {
        override fun yaml(): Yaml = Yaml(SafeConstructor(loaderOptions()))

        @Suppress("UNCHECKED_CAST")
        override fun mapping(loaded: Any?): Map<String, Any> =
            loaded as? Map<String, Any> ?: throw IllegalArgumentException("not_a_mapping: $loaded")
    };

    fun dump(document: Any): String = yaml().dump(document)

    fun dump(document: Any, into: Writer) = yaml().dump(document, into)

    fun load(text: String): Map<String, Any> = mapping(yaml().load<Any?>(text))

    protected abstract fun yaml(): Yaml

    protected abstract fun mapping(loaded: Any?): Map<String, Any>

    companion object {
        // SnakeYAML's 3 MiB default refuses host requirements files (3.76 MB measured); 16 MiB still refuses a runaway file.
        const val CODE_POINT_LIMIT = 16 * 1024 * 1024
    }
}
