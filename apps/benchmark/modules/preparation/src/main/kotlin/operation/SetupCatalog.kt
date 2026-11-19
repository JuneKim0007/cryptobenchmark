package io.github.junekim0007.cryptobench.preparation.operation

import io.github.junekim0007.cryptobench.settings.EngineRows
import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.measurement.Variant
import io.github.junekim0007.cryptobench.document.DocumentFields
import io.github.junekim0007.cryptobench.document.YamlCodec
import java.util.Locale

/** setup-catalog.yaml: per engine type, cipher mode or name suffix, what a fixed call still does; notFixed always makes the instance per call. */
internal class SetupCatalog(document: Map<String, Any>) {

    val rows = EngineRows(document)

    /** The asked paths this type's row applies, then the asked ones it does not. */
    fun paths(type: String, asked: List<Variant>): Pair<List<Variant>, List<Variant>> =
        asked.partition { it.label in rows.applicable(type) }

    // hasIv is asked only for a cipher transformation without a mode
    fun perCall(case: BenchmarkCase, hasIv: () -> Boolean = { false }): PerCall {
        val row = DocumentFields.asSection(rows.row(case.type) ?: throw IllegalArgumentException(EngineRows.notInCatalogue(case.type)), "engines.${case.type}")
        if (single(case.type)) return PerCall.OPERATION
        if (case.variant == Variant.NOT_FIXED) return PerCall.INSTANCE_INIT_AND_OPERATION
        val fixed = DocumentFields.string(row, FIXED)
        if (fixed == BY_SUFFIX) return bySuffix(row, case.algorithm.uppercase(Locale.ROOT))
        if (fixed != BY_MODE) return PerCall.of(fixed)
        val mode = case.algorithm.split('/').getOrNull(1)?.uppercase(Locale.ROOT)
            ?: return PerCall.of(DocumentFields.string(DocumentFields.section(row, "withoutMode"), if (hasIv()) "iv" else "noIv"))
        val modes = DocumentFields.section(row, "modes").mapKeys { it.key.uppercase(Locale.ROOT) }
        return PerCall.of(modes[mode]?.toString() ?: DocumentFields.string(row, "otherMode"))
    }

    /** A generator times its generation after one init: its row must leave nothing else in the call. */
    fun initOnce(case: BenchmarkCase): PerCall = perCall(case).also {
        require(it == PerCall.OPERATION) { "not_supported: ${case.type} times its generation after one init; $RESOURCE gives ${case.variant.label} ${it.label}" }
    }

    private fun bySuffix(row: Map<String, Any>, algorithm: String): PerCall {
        val suffixes = DocumentFields.section(row, "suffixes").entries.firstOrNull { algorithm.endsWith(it.key.uppercase(Locale.ROOT)) }
        return PerCall.of(suffixes?.value?.toString() ?: DocumentFields.string(row, "otherSuffix"))
    }

    // a type with no notFixed path makes its instance once: the call is the operation alone
    private fun single(type: String): Boolean = Variant.NOT_FIXED.label !in rows.applicable(type)

    companion object {

        private const val FIXED = "fixed"
        private const val BY_MODE = "byMode"
        private const val BY_SUFFIX = "bySuffix"
        const val RESOURCE = EngineRows.RESOURCE

        val standard: SetupCatalog by lazy {
            val text = SetupCatalog::class.java.getResourceAsStream(RESOURCE)?.use { it.readBytes().toString(Charsets.UTF_8) }
                ?: throw IllegalStateException("missing_resource: $RESOURCE beside ${SetupCatalog::class.java.name}")
            SetupCatalog(YamlCodec.DOCUMENT.load(text))
        }
    }
}
