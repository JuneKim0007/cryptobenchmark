package io.github.junekim0007.cryptobench.preparation.resolve

import io.github.junekim0007.cryptobench.catalogue.EngineRows
import io.github.junekim0007.cryptobench.files.VariantLabels
import io.github.junekim0007.cryptobench.preparation.engine.EngineTypes
import io.github.junekim0007.cryptobench.preparation.key.secure.KeystoreSpec
import io.github.junekim0007.cryptobench.preparation.measurement.Variant
import io.github.junekim0007.cryptobench.preparation.request.Selection
import io.github.junekim0007.cryptobench.preparation.operation.SetupCatalog
import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.jca.bind.ParameterBinder
import io.github.junekim0007.cryptobench.preparation.port.Availability
import io.github.junekim0007.cryptobench.preparation.port.DeviceCapability
import io.github.junekim0007.cryptobench.preparation.request.BenchmarkRequest

class CaseResolver(
    private val capability: DeviceCapability,
    binder: ParameterBinder,
    private val engineTypes: EngineTypes = EngineTypes.standard(),
) {

    private val selectionCheck = SelectionCheck(binder)

    fun resolve(request: BenchmarkRequest): Resolution {
        val cases = mutableListOf<BenchmarkCase>()
        val rejections = mutableListOf<Rejection>()
        for (selection in request.selections) {
            val operations = engineTypes.operationsOf(selection.type)
            val problem = selectionCheck.problem(selection, operations)
            if (problem != null) {
                rejections += Rejection(selection, null, problem)
                continue
            }
            if (SetupCatalog.standard.rows.row(selection.type) == null) {
                rejections += Rejection(selection, null, EngineRows.notInCatalogue(selection.type))
                continue
            }
            val asked = selection.variants ?: request.global.variants
            val (applicable, dropped) = SetupCatalog.standard.paths(selection.type, asked)
            val secureRefusal = secureRefusal(selection, applicable).takeIf { Variant.SECURE in applicable }
            val variants = if (secureRefusal == null) applicable else applicable - Variant.SECURE
            // a refused secure path the entry wrote is one line; the run's drops quietly unless nothing is left
            if (secureRefusal != null && (selection.variants?.contains(Variant.SECURE) == true || variants.isEmpty())) {
                rejections += Rejection(selection, selection.provider, secureRefusal)
            }
            if (variants.isEmpty()) {
                if (secureRefusal == null) rejections += Rejection(selection, null,
                    VariantLabels.notApplicable(subject(selection), SetupCatalog.standard.rows.applicable(selection.type), dropped.map { it.label }))
                continue
            }
            if (selection.keySource.backing != null && Variant.SECURE !in variants) {
                rejections += Rejection(selection, null, "unused_setting: key.backing reaches no ${Variant.SECURE.label} case")
                continue
            }
            val availability = capability.check(selection.provider, selection.type, selection.algorithm)
            // a registered generator whose default-run trial failed is measured only where its key is born inside it
            val runnable = when {
                availability == Availability.Available -> variants
                availability is Availability.Unavailable && availability.registered -> variants.filter { it == Variant.SECURE }
                else -> emptyList()
            }
            if (runnable.size < variants.size) rejections += Rejection(selection, selection.provider, (availability as Availability.Unavailable).reason)
            if (runnable.isNotEmpty()) cases += SelectionExpander.expand(request.global, selection, operations, runnable)
        }
        return Resolution(cases, rejections)
    }

    // this runtime lacks the keystore classes, or the guide gives the provider no keystore block (it keeps no key inside)
    private fun secureRefusal(selection: Selection, applicable: List<Variant>): String? = KeystoreSpec.missing()
        ?: VariantLabels.notApplicable("${subject(selection)} without a guide keystore block", (applicable - Variant.SECURE).map { it.label }, listOf(Variant.SECURE.label))
            .takeIf { selection.keystore.isEmpty() }

    private fun subject(selection: Selection) = "${selection.provider}.${selection.type}.${selection.algorithm}"
}
