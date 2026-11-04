package io.github.junekim0007.cryptobench.preparation.operation

import io.github.junekim0007.cryptobench.preparation.engine.EngineTypeName
import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.measurement.Variant
import io.github.junekim0007.cryptobench.preparation.shared.DocumentFields
import io.github.junekim0007.cryptobench.preparation.shared.YamlCodec
import java.util.Locale

/** setup-catalog.yaml: per engine type and cipher mode, what a fixed call still does; notFixed always makes the instance per call. */
internal class SetupCatalog(document: Map<String, Any>) {

    private val engines: Map<String, Map<String, Any>> = DocumentFields.section(document, "engines")
        .entries.associate { (type, row) -> EngineTypeName.fold(type) to DocumentFields.asSection(row, "engines.$type") }

    fun variantsOf(type: String, selected: List<Variant>): List<Variant> =
        if (single(type)) listOf(Variant.FIXED) else selected

    // hasIv is asked only for a cipher transformation without a mode
    fun perCall(case: BenchmarkCase, hasIv: () -> Boolean = { false }): PerCall {
        if (single(case.type)) return PerCall.OPERATION
        if (case.variant == Variant.NOT_FIXED) return PerCall.INSTANCE_INIT_AND_OPERATION
        val row = engines.getValue(EngineTypeName.fold(case.type))
        val fixed = DocumentFields.string(row, FIXED)
        if (fixed != BY_MODE) return PerCall.of(fixed)
        val mode = case.algorithm.split('/').getOrNull(1)?.uppercase(Locale.ROOT)
            ?: return PerCall.of(DocumentFields.string(DocumentFields.section(row, "withoutMode"), if (hasIv()) "iv" else "noIv"))
        val modes = DocumentFields.section(row, "modes").mapKeys { it.key.uppercase(Locale.ROOT) }
        return PerCall.of(modes[mode]?.toString() ?: DocumentFields.string(row, "otherMode"))
    }

    private fun single(type: String): Boolean {
        val row = engines[EngineTypeName.fold(type)] ?: return true
        return row["variants"] == "one"
    }

    companion object {

        private const val FIXED = "fixed"
        private const val BY_MODE = "byMode"
        const val RESOURCE = "setup-catalog.yaml"

        val standard: SetupCatalog by lazy {
            val text = SetupCatalog::class.java.getResourceAsStream(RESOURCE)?.use { it.readBytes().toString(Charsets.UTF_8) }
                ?: throw IllegalStateException("missing_resource: $RESOURCE beside ${SetupCatalog::class.java.name}")
            SetupCatalog(YamlCodec().load(text))
        }
    }
}
