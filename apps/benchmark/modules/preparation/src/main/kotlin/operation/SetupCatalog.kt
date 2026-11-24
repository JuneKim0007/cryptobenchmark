package io.github.junekim0007.cryptobench.preparation.operation

import io.github.junekim0007.cryptobench.catalogue.EngineRows
import io.github.junekim0007.cryptobench.document.names.AlgorithmNames
import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.measurement.Variant
import io.github.junekim0007.cryptobench.document.DocumentFields
import io.github.junekim0007.cryptobench.document.YamlCodec
import io.github.junekim0007.cryptobench.document.catalogue.FamilyCatalogue

/** setup-catalog.yaml: per engine type what a fixed call still does, a byMode or bySuffix type's catalogued entry by its catalogue rows as its provider's build sees them; notFixed always makes the instance per call. */
internal class SetupCatalog(document: Map<String, Any>, private val catalogue: FamilyCatalogue = FamilyCatalogue(emptyList())) {

    val rows = EngineRows(document)

    /** The asked paths this type's row applies, then the asked ones it does not. */
    fun paths(type: String, asked: List<Variant>): Pair<List<Variant>, List<Variant>> =
        asked.partition { it.label in rows.applicable(type) }

    // hasIv is asked only for an uncatalogued cipher transformation without a mode
    fun perCall(case: BenchmarkCase, platform: String? = null, hasIv: () -> Boolean = { false }): PerCall {
        val row = DocumentFields.asSection(rows.row(case.type) ?: throw IllegalArgumentException(EngineRows.notInCatalogue(case.type)), "engines.${case.type}")
        if (single(case.type)) return PerCall.OPERATION
        if (case.variant == Variant.NOT_FIXED) return PerCall.INSTANCE_INIT_AND_OPERATION
        val fixed = DocumentFields.string(row, FIXED)
        if (fixed == BY_SUFFIX || fixed == BY_MODE) catalogued(case, platform)?.let { return it }
        if (fixed == BY_SUFFIX) return bySuffix(row, AlgorithmNames.fold(case.algorithm))
        if (fixed != BY_MODE) return PerCall.of(fixed)
        val mode = case.algorithm.split('/').getOrNull(1)?.let(AlgorithmNames::fold)
            ?: return PerCall.of(DocumentFields.string(DocumentFields.section(row, "withoutMode"), if (hasIv()) "iv" else "noIv"))
        val modes = DocumentFields.section(row, "modes").mapKeys { AlgorithmNames.fold(it.key) }
        return PerCall.of(modes[mode]?.toString() ?: DocumentFields.string(row, "otherMode"))
    }

    /** A generator times its generation after one init: its row must leave nothing else in the call. */
    fun initOnce(case: BenchmarkCase): PerCall = perCall(case).also {
        require(it == PerCall.OPERATION) { "not_supported: ${case.type} times its generation after one init; $RESOURCE gives ${case.variant.label} ${it.label}" }
    }

    // an init value that must not repeat, or a provider that refuses a second operation, makes init part of every call; a provider with no measured build is the row's
    private fun catalogued(case: BenchmarkCase, platform: String?): PerCall? {
        val entry = catalogue.of(case.type, case.algorithm) ?: return null
        val fields = entry.fields(catalogue.build(case.provider, platform) ?: return null)
        val fresh = (fields[REQUIRED] as? List<*>).orEmpty().filterIsInstance<Map<*, *>>().any { it[PASSED_TO] == INIT && it[RULE] in FRESH }
        val forward = ((((fields[LIFECYCLE] as? Map<*, *>)?.get(RESET) as? Map<*, *>)?.get(FORWARD) as? Map<*, *>)?.get(VALUE))
        return if (fresh || forward == NONE) PerCall.INIT_AND_OPERATION else PerCall.OPERATION
    }

    private fun bySuffix(row: Map<String, Any>, algorithm: String): PerCall {
        val suffixes = DocumentFields.section(row, "suffixes").entries.firstOrNull { algorithm.endsWith(AlgorithmNames.fold(it.key)) }
        return PerCall.of(suffixes?.value?.toString() ?: DocumentFields.string(row, "otherSuffix"))
    }

    // a type with no notFixed path makes its instance once: the call is the operation alone
    private fun single(type: String): Boolean = Variant.NOT_FIXED.label !in rows.applicable(type)

    companion object {

        private const val FIXED = "fixed"
        private const val BY_MODE = "byMode"
        private const val BY_SUFFIX = "bySuffix"
        const val RESOURCE = EngineRows.RESOURCE
        private const val REQUIRED = "required"
        private const val PASSED_TO = "passedTo"
        private const val INIT = "init"
        private const val RULE = "rule"
        private val FRESH = setOf("unique", "unpredictable")
        private const val LIFECYCLE = "lifecycle"
        private const val RESET = "reset"
        private const val FORWARD = "forward"
        private const val VALUE = "value"
        private const val NONE = "none"

        val standard: SetupCatalog by lazy {
            val text = SetupCatalog::class.java.getResourceAsStream(RESOURCE)?.use { it.readBytes().toString(Charsets.UTF_8) }
                ?: throw IllegalStateException("missing_resource: $RESOURCE beside ${SetupCatalog::class.java.name}")
            SetupCatalog(YamlCodec.DOCUMENT.load(text), FamilyCatalogue.bundled(FamilyCatalogue.KEYED))
        }
    }
}
