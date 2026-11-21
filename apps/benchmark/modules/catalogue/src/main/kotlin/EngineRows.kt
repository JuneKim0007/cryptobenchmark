package io.github.junekim0007.cryptobench.catalogue

import io.github.junekim0007.cryptobench.files.FileNames
import io.github.junekim0007.cryptobench.files.VariantLabels
import java.util.Locale

/** setup-catalog.yaml's per-type rows, config's and preparation's one reading: the paths a type applies, the key generators. */
class EngineRows(document: Map<String, *>) {

    private val rows: Map<String, Pair<String, Map<String, *>>> = section(document[ENGINES], ENGINES).entries
        .associate { (type, row) -> fold(type) to (type to section(row, "$ENGINES.$type")) }

    /** The row of [type], or null when the catalogue lacks it. */
    fun row(type: String): Map<String, *>? = rows[fold(type)]?.second

    /** A row's `variants`, or [fixed, notFixed] without one; a type the catalogue lacks applies none. */
    fun applicable(type: String): List<String> {
        val row = row(type) ?: return emptyList()
        val paths = row[VARIANTS] ?: return OPERATION
        val names = (paths as? List<*>)?.map { it.toString() }
        require(names != null && names.isNotEmpty() && names.all { it in PATHS } && names.distinct() == names) {
            "invalid: $RESOURCE $ENGINES.$type.$VARIANTS $paths, distinct names of $PATHS"
        }
        return names
    }

    /** The types whose row generates a key, in catalogue order. */
    val generators: List<String> = rows.values.filter { (_, row) -> GENERATES in row }.map { it.first }

    /** The one type whose row generates [kind] (secretKey, keyPair). */
    fun generator(kind: String): String {
        val types = rows.values.filter { (_, row) -> row[GENERATES]?.toString() == kind }.map { it.first }
        return types.singleOrNull() ?: throw IllegalArgumentException("invalid: $RESOURCE $ENGINES name ${types.ifEmpty { "no type" }} with $GENERATES: $kind, exactly one wanted")
    }

    /** The types whose row applies [path], in catalogue order. */
    fun taking(path: String): List<String> = rows.values.map { it.first }.filter { path in applicable(it) }

    companion object {
        const val RESOURCE = FileNames.SETUP_CATALOG
        const val SECRET_KEY = "secretKey"
        const val KEY_PAIR = "keyPair"
        private const val ENGINES = "engines"
        private const val VARIANTS = "variants"
        private const val GENERATES = "generates"
        private val PATHS = listOf(VariantLabels.FIXED, VariantLabels.NOT_FIXED, VariantLabels.SECURE)
        private val OPERATION = listOf(VariantLabels.FIXED, VariantLabels.NOT_FIXED)

        /** The refusal of a type the catalogue lacks. */
        fun notInCatalogue(type: String): String = "not_in_catalogue: $type has no row in $RESOURCE"

        private fun fold(type: String) = type.uppercase(Locale.ROOT)

        private fun section(value: Any?, path: String): Map<String, *> {
            val map = value as? Map<*, *> ?: throw IllegalArgumentException(if (value == null) "missing_field: $RESOURCE $path" else "wrong_type: $RESOURCE $path")
            return map.entries.associate { (key, row) -> key.toString() to row }
        }
    }
}
