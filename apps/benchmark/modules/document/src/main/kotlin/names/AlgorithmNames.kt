package io.github.junekim0007.cryptobench.document.names

import io.github.junekim0007.cryptobench.document.versioned.DocumentReader
import io.github.junekim0007.cryptobench.document.versioned.YamlFiles
import io.github.junekim0007.cryptobench.document.names.dto.Canonical
import java.io.File
import java.util.Locale

class AlgorithmNames private constructor(
    private val names: Map<String, Map<String, String>>,
    private val sized: Map<String, Map<String, Canonical>>,
    private val transformations: Map<String, Transformation>,
    private val keyTypes: Map<String, String>,
    private val captured: Map<Pair<String, String>, Canonical> = emptyMap(),
    // (type, folded alias) -> who means what, as NameLayers merged it
    val conflicts: Map<Pair<String, String>, String> = emptyMap(),
) {

    private class Transformation(
        val modes: Map<String, String>,
        val paddings: Map<String, String>,
        val paddingSynonyms: Map<String, Map<String, String>>,
        val modeSynonyms: Map<String, Map<String, String>>,
    )

    /** The names file's answer only, never a capture alias. */
    fun catalogued(type: String, name: String): Canonical {
        val single = single(type, name)
        if (single.known || type !in transformations || '/' !in name) {
            return single
        }
        return transformation(type, name)
    }

    /** A user-written name: the names file wins over any capture alias; a capture alias providers mean apart refuses name_conflict. */
    fun canonical(type: String, name: String): Canonical {
        val found = catalogued(type, name)
        if (found.known) return found
        conflicts[type to fold(name)]?.let { throw IllegalArgumentException("$NAME_CONFLICT: $type $name: $it") }
        return captured[type to fold(name)] ?: found
    }

    /** A registered name: a name_conflict keys by its own spelling, never a stop. */
    fun keyOrSpelling(type: String, name: String): Pair<String, Int?> = registered(type, name).key

    /** The conflict of a capture alias the names file knows: the names file's answer stands. */
    fun aliasConflict(type: String, name: String): String? = conflicts[type to fold(name)]?.takeIf { catalogued(type, name).known }

    /** The key type a Key.getAlgorithm() spelling or a catalogue key.type names. */
    fun keyType(name: String): Canonical = keyTypes[fold(name)]?.let { Canonical(it) } ?: Canonical(name, null, false)

    fun key(type: String, name: String): Pair<String, Int?> = canonical(type, name).key

    fun matches(type: String, pattern: String, name: String): Boolean {
        if ('*' !in pattern) {
            return key(type, pattern) == keyOrSpelling(type, name)
        }
        val glob = Regex(pattern.split('*').joinToString(".*") { Regex.escape(it) }, RegexOption.IGNORE_CASE)
        return glob.matches(name) || glob.matches(registered(type, name).name)
    }

    internal fun layered(captured: Map<Pair<String, String>, Canonical>, conflicts: Map<Pair<String, String>, String>): AlgorithmNames =
        AlgorithmNames(names, sized, transformations, keyTypes, captured, conflicts)

    private fun registered(type: String, name: String): Canonical =
        if (!catalogued(type, name).known && (type to fold(name)) in conflicts) Canonical(name, null, false) else canonical(type, name)

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

    companion object : DocumentReader<AlgorithmNames> {

        const val FILE = "name-index.yaml"
        private const val SCHEMA_VERSION = 2
        private const val OID_PREFIX = "OID."
        const val NAME_CONFLICT = "name_conflict"
        const val SPELLINGS = "spellings"

        override val schemaVersion: Int = SCHEMA_VERSION

        val catalog: AlgorithmNames by lazy {
            val text = AlgorithmNames::class.java.getResource(FILE)?.readText()
                ?: throw IllegalStateException("names_catalog_missing: $FILE is not beside ${AlgorithmNames::class.java.name}")
            read(text)
        }

        fun fold(value: String): String = value.uppercase(Locale.ROOT)

        fun read(text: String): AlgorithmNames = YamlFiles().readOnly(File(FILE), this).read(text)

        @Suppress("UNCHECKED_CAST")
        override fun parse(document: Map<String, Any>): AlgorithmNames {
            val written = document[SPELLINGS] as? Map<String, Map<String, List<String>?>> ?: throw IllegalArgumentException("names_schema: no $SPELLINGS: section")
            val names = written.mapValues { (_, spellings) -> folded(spellings) }
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

internal val Canonical.key: Pair<String, Int?> get() = AlgorithmNames.fold(name) to keySize
