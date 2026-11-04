package io.github.junekim0007.cryptobench.config.names

import io.github.junekim0007.cryptobench.config.names.dto.Canonical
import io.github.junekim0007.cryptobench.config.yaml.YamlCodec
import java.util.Locale

class AlgorithmNames private constructor(
    private val names: Map<String, Map<String, String>>,
    private val sized: Map<String, Map<String, Canonical>>,
    private val transformations: Map<String, Transformation>,
) {

    private class Transformation(
        val modes: Map<String, String>,
        val paddings: Map<String, String>,
        val paddingSynonyms: Map<String, Map<String, String>>,
        val modeSynonyms: Map<String, Map<String, String>>,
    )

    fun canonical(type: String, name: String): Canonical {
        val single = single(type, name)
        if (single.known || type !in transformations || '/' !in name) {
            return single
        }
        return transformation(type, name)
    }

    fun key(type: String, name: String): Pair<String, Int?> = canonical(type, name).let { fold(it.name) to it.keySize }

    fun matches(type: String, pattern: String, name: String): Boolean {
        if ('*' !in pattern) {
            return key(type, pattern) == key(type, name)
        }
        val glob = Regex(pattern.split('*').joinToString(".*") { Regex.escape(it) }, RegexOption.IGNORE_CASE)
        return glob.matches(name) || glob.matches(canonical(type, name).name)
    }

    private fun single(type: String, name: String): Canonical {
        sized[type]?.get(fold(name))?.let { return it }
        return names[type]?.get(fold(name))?.let { Canonical(it) } ?: Canonical(name, null, false)
    }

    private fun transformation(type: String, name: String): Canonical {
        val parts = name.split("/", limit = 3)
        if (parts.size != 3) {
            return Canonical(name, null, false)
        }
        val base = single(type, parts[0])
        val rules = transformations.getValue(type)
        val algorithm = fold(base.name)
        val mode = rules.modeSynonyms[algorithm]?.get(fold(parts[1])) ?: rules.modes[fold(parts[1])]
        val padding = rules.paddingSynonyms[algorithm]?.get(fold(parts[2])) ?: rules.paddings[fold(parts[2])]
        if (!base.known || mode == null || padding == null) {
            return Canonical(name, null, false)
        }
        return Canonical("${base.name}/$mode/$padding", base.keySize)
    }

    companion object {

        const val RESOURCE = "/algorithm-names.yaml"
        private const val SCHEMA_VERSION = 1

        val catalog: AlgorithmNames by lazy {
            val text = AlgorithmNames::class.java.getResource(RESOURCE)?.readText()
                ?: throw IllegalStateException("names_catalog_missing: $RESOURCE is not on the classpath")
            parse(YamlCodec().load(text))
        }

        fun fold(value: String): String = value.uppercase(Locale.ROOT)

        @Suppress("UNCHECKED_CAST")
        fun parse(document: Map<String, Any>): AlgorithmNames {
            require(document["schemaVersion"] == SCHEMA_VERSION) { "names_schema: schemaVersion ${document["schemaVersion"]} is not $SCHEMA_VERSION" }
            val names = (document["names"] as Map<String, Map<String, List<String>?>>).mapValues { (_, spellings) -> folded(spellings) }
            val sized = (document["sized"] as Map<String, Map<String, Map<String, Any>>>? ?: emptyMap()).mapValues { (_, rows) ->
                rows.entries.associate { (spelling, row) -> fold(spelling) to Canonical(row["name"] as String, row["keySize"] as Int) }
            }
            val transformations = (document["transformations"] as Map<String, Map<String, Any>>? ?: emptyMap()).mapValues { (_, rules) ->
                Transformation(
                    folded((rules["modes"] as List<String>).associateWith { null }),
                    folded((rules["paddings"] as List<String>).associateWith { null }),
                    synonyms(rules["paddingSynonyms"] as Map<String, Map<String, String>>?),
                    synonyms(rules["modeSynonyms"] as Map<String, Map<String, String>>?),
                )
            }
            return AlgorithmNames(names, sized, transformations)
        }

        private fun folded(spellings: Map<String, List<String>?>): Map<String, String> {
            val table = linkedMapOf<String, String>()
            for ((canonical, aliases) in spellings) {
                for (spelling in listOf(canonical) + aliases.orEmpty()) {
                    val prior = table.getOrPut(fold(spelling)) { canonical }
                    require(prior == canonical) { "names_catalog_duplicate: $spelling is under $prior and $canonical" }
                }
            }
            return table
        }

        private fun synonyms(table: Map<String, Map<String, String>>?): Map<String, Map<String, String>> =
            table.orEmpty().entries.associate { (algorithm, pairs) -> fold(algorithm) to pairs.mapKeys { fold(it.key) } }
    }
}
