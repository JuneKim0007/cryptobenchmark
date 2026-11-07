package io.github.junekim0007.cryptobench.preparation.resolve

import io.github.junekim0007.cryptobench.preparation.engine.EngineTypes
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
        for (selection in request.selections) {
            val operations = engineTypes.operationsOf(selection.type)
            val problem = selectionCheck.problem(selection, operations)
            if (problem != null) {
                rejections += Rejection(selection, null, problem)
                continue
            }
            when (val availability = capability.check(selection.provider, selection.type, selection.algorithm)) {
                Availability.Available -> cases += SelectionExpander.expand(request.global, selection, operations)
                is Availability.Unavailable -> rejections += Rejection(selection, selection.provider, availability.reason)
            }
        }
        return Resolution(cases, rejections)
    }
}
