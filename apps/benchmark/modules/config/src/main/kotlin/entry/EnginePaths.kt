package io.github.junekim0007.cryptobench.config.entry

import io.github.junekim0007.cryptobench.config.names.AlgorithmNames
import io.github.junekim0007.cryptobench.document.DocumentFields
import io.github.junekim0007.cryptobench.document.YamlCodec
import io.github.junekim0007.cryptobench.files.FileNames

/** setup-catalog.yaml's per-type rows as config reads them: the paths a type applies and the types that generate keys. */
class EnginePaths(document: Map<String, Any>) {

    private val rows: Map<String, Pair<String, Map<String, Any>>> = DocumentFields.section(document, "engines")
        .entries.associate { (type, row) -> AlgorithmNames.fold(type) to (type to DocumentFields.asSection(row, "engines.$type")) }

    /** A row's `variants`, or [fixed, notFixed] without one; a type the catalogue lacks applies none. */
    fun applicable(type: String): List<String> {
        val row = rows[AlgorithmNames.fold(type)]?.second ?: return emptyList()
        if (VARIANTS !in row) return OPERATION
        val paths = DocumentFields.strings(row, VARIANTS)
        require(paths.isNotEmpty() && Variants.valid(paths)) { "invalid: $RESOURCE engines.$type.$VARIANTS $paths, distinct names of ${Variants.NAMES}" }
        return paths
    }

    val generators: List<String> = rows.values.filter { (_, row) -> GENERATES in row }.map { it.first }

    /** The types whose row applies [path], in catalogue order. */
    fun taking(path: String): List<String> = rows.values.map { it.first }.filter { path in applicable(it) }

    companion object {

        const val RESOURCE = "/" + FileNames.SETUP_CATALOG
        private const val VARIANTS = "variants"
        private const val GENERATES = "generates"
        private val OPERATION = listOf(Variants.FIXED, Variants.NOT_FIXED)

        val catalog: EnginePaths by lazy {
            val text = EnginePaths::class.java.getResource(RESOURCE)?.readText()
                ?: throw IllegalStateException("missing_resource: $RESOURCE is not on the classpath")
            EnginePaths(YamlCodec.DOCUMENT.load(text))
        }
    }
}
