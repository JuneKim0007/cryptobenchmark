package io.github.junekim0007.cryptobench.preparation.resolve

import io.github.junekim0007.cryptobench.preparation.engine.EngineTypes
import io.github.junekim0007.cryptobench.preparation.operation.SetupCatalog
import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.parameter.bind.ParameterBinder
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
        val notices = mutableListOf<String>()
        for (selection in request.selections) {
            val operations = engineTypes.operationsOf(selection.type)
            val problem = selectionCheck.problem(selection, operations)
            if (problem != null) {
                rejections += Rejection(selection, null, problem)
                continue
            }
            val asked = selection.variants ?: request.global.variants
            val (variants, dropped) = SetupCatalog.standard.paths(selection.type, asked)
            val notApplicable = "path_not_applicable: ${selection.provider}.${selection.type}.${selection.algorithm} applies ${SetupCatalog.standard.applicable(selection.type)}, ${dropped.map { it.label }} dropped"
            if (variants.isEmpty()) {
                rejections += Rejection(selection, null, notApplicable)
                continue
            }
            when (val availability = capability.check(selection.provider, selection.type, selection.algorithm)) {
                Availability.Available -> {
                    cases += SelectionExpander.expand(request.global, selection, operations, variants)
                    // only a path the entry wrote itself is noted; the run's paths a row lacks are dropped quietly
                    if (dropped.isNotEmpty() && selection.variants != null) notices += notApplicable
                }
                is Availability.Unavailable -> rejections += Rejection(selection, selection.provider, availability.reason)
            }
        }
        return Resolution(cases, rejections, notices)
    }
}
