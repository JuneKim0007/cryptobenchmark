package io.github.junekim0007.cryptobench.benchmark.preparation.resolve

import io.github.junekim0007.cryptobench.benchmark.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.benchmark.preparation.parameter.bind.ParameterBinder
import io.github.junekim0007.cryptobench.benchmark.preparation.port.Availability
import io.github.junekim0007.cryptobench.benchmark.preparation.port.DeviceCapability
import io.github.junekim0007.cryptobench.benchmark.preparation.request.BenchmarkRequest
import io.github.junekim0007.cryptobench.benchmark.preparation.request.Selection

/** Request × device → cases. Rejects by name, before anything runs; never calls the JCA itself. */
class CaseResolver(
    private val capability: DeviceCapability,
    private val rules: AxisRules = AxisRules.standard(),
    binder: ParameterBinder = ParameterBinder(),
) {

    private val parameterCheck = ParameterCheck(binder)

    fun resolve(request: BenchmarkRequest): Resolution {
        val cases = mutableListOf<BenchmarkCase>()
        val rejections = mutableListOf<Rejection>()
        for (selection in request.selections) {
            val problem = parameterCheck.problem(selection)
            if (problem != null) {
                rejections += Rejection(selection, null, problem)
                continue
            }
            val providers = providersFor(selection, rejections)
            cases += SelectionExpander.expand(request, selection, providers, rules.of(selection.type))
        }
        return Resolution(cases, rejections)
    }

    private fun providersFor(selection: Selection, rejections: MutableList<Rejection>): List<String> {
        val candidates = selection.providers.ifEmpty { capability.providers() }
        val available = candidates.filter { provider ->
            when (val availability = capability.check(provider, selection.type, selection.algorithm)) {
                Availability.Available -> true
                is Availability.Unavailable -> {
                    if (selection.providers.isNotEmpty()) {
                        rejections += Rejection(selection, provider, availability.reason)
                    }
                    false
                }
            }
        }
        if (available.isEmpty() && selection.providers.isEmpty()) {
            rejections += Rejection(selection, null, "no_provider")
        }
        return available
    }
}
