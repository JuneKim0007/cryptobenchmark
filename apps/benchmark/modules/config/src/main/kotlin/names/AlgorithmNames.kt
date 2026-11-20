package io.github.junekim0007.cryptobench.config.names

import io.github.junekim0007.cryptobench.document.SchemaVersion
import io.github.junekim0007.cryptobench.config.names.dto.Canonical
import io.github.junekim0007.cryptobench.document.YamlCodec
import io.github.junekim0007.cryptobench.files.FileNames
import java.util.Locale

class AlgorithmNames private constructor(
    private val names: Map<String, Map<String, String>>,
    private val sized: Map<String, Map<String, Canonical>>,
    private val transformations: Map<String, Transformation>,
    private val keyTypes: Map<String, String>,
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

    /** The key type a Key.getAlgorithm() spelling or a catalogue key.type names. */
    fun keyType(name: String): Canonical = keyTypes[fold(name)]?.let { Canonical(it) } ?: Canonical(name, null, false)

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
        // a base that is itself a whole transformation (ELGAMAL -> ELGAMAL/NONE/NoPadding) composes nothing
        if (!base.known || '/' in base.name || mode == null || padding == null) {
            return Canonical(name, null, false)
        }
        return Canonical("${base.name}/$mode/$padding", base.keySize)
    }

    companion object {

        const val RESOURCE = "/" + FileNames.ALGORITHM_NAMES
        private const val SCHEMA_VERSION = 1
        private const val OID_PREFIX = "OID."

        val catalog: AlgorithmNames by lazy {
            val text = AlgorithmNames::class.java.getResource(RESOURCE)?.readText()
                ?: throw IllegalStateException("names_catalog_missing: $RESOURCE is not on the classpath")
            parse(YamlCodec.DOCUMENT.load(text))
        }

        fun fold(value: String): String = value.uppercase(Locale.ROOT)

        @Suppress("UNCHECKED_CAST")
        fun parse(document: Map<String, Any>): AlgorithmNames {
            SchemaVersion.require(document, SCHEMA_VERSION, FileNames.ALGORITHM_NAMES)
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
            checkLinks(names, sized)
            return AlgorithmNames(names, sized, transformations, folded(document["keyTypes"] as Map<String, List<String>?>? ?: emptyMap()))
        }

        // a spelling is sized or named, never both; an OID. spelling names what its bare OID names
        private fun checkLinks(names: Map<String, Map<String, String>>, sized: Map<String, Map<String, Canonical>>) {
            val both = sized.flatMap { (type, rows) -> rows.keys.filter { it in names[type].orEmpty() }.map { "$type $it is sized and named" } }
            require(both.isEmpty()) { "names_catalog_duplicate: " + both.joinToString("; ") }
            val split = (names.keys + sized.keys).sorted().flatMap { type ->
                val target = names[type].orEmpty().mapValues { (_, c) -> c to null } + sized[type].orEmpty().mapValues { (_, c) -> c.name to c.keySize }
                target.filter { (s, t) -> s.startsWith(OID_PREFIX) && (target[s.removePrefix(OID_PREFIX)] ?: t) != t }
                    .map { (s, t) -> "$type $s is $t, ${s.removePrefix(OID_PREFIX)} is ${target[s.removePrefix(OID_PREFIX)]}" }
            }
            require(split.isEmpty()) { "names_oid_split: " + split.joinToString("; ") }
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
