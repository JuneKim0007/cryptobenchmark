package io.github.junekim0007.cryptobench.discovery.trial.requirement

import io.github.junekim0007.cryptobench.discovery.contract.ServiceRequirement

// Level 2 already called the generator at its default and beside it: this reads that record instead of paying for the keys twice.
internal object GeneratorFacts : RequirementCall {

    override fun measure(service: ProbedService, sheet: FactSheet): CallResult {
        val run = service.trial.defaultRun ?: return CallResult(ServiceRequirement.GENERATION_REFUSED, "no default run")
        if (!run.works) return CallResult(ServiceRequirement.GENERATION_REFUSED, ErrorText.clean(run.error))
        sheet.measure("defaultBits") { run.keySize }
        sheet.measure("keyMaterial") { run.keyMaterial.ifEmpty { null } }
        sheet.measure("keyFormat") { run.keyFormat.ifEmpty { null } }
        sheet.measure("sizes") {
            run.triedKeys.takeIf { it.isNotEmpty() }?.let { tried ->
                linkedMapOf("accepted" to Sweep.ranges(tried.filter { !it.refused }.map { it.size }), "refused" to Sweep.ranges(tried.filter { it.refused }.map { it.size }))
            }
        }
        return CallResult(runWith = mapOf("operation" to "generate"))
    }
}
