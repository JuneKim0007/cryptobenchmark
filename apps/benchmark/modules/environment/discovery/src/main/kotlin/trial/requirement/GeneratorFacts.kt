package io.github.junekim0007.cryptobench.discovery.trial.requirement

import io.github.junekim0007.cryptobench.discovery.contract.ServiceKey
import io.github.junekim0007.cryptobench.discovery.contract.ServiceRequirement
import io.github.junekim0007.cryptobench.discovery.trial.call.GeneratorCall
import java.security.KeyPairGenerator
import javax.crypto.KeyGenerator

// Level 2 already called the generator at its default and beside it: this reads that record instead of paying for the keys twice.
internal object GeneratorFacts : RequirementCall {

    override fun instance(service: ProbedService) {
        if (ServiceKey.fold(service.type) == PAIR) KeyPairGenerator.getInstance(service.algorithm, service.provider)
        else KeyGenerator.getInstance(service.algorithm, service.provider)
    }

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
        sheet.measure("reset") { reset(service) }
        return CallResult(runWith = mapOf("operation" to "generate"))
    }

    private fun reset(service: ProbedService): Map<String, Any> {
        val pair = ServiceKey.fold(service.type) == PAIR
        val generate = CallStep<() -> Unit>(if (pair) "generateKeyPair" else "generateKey") { it(); null }
        val make = { GeneratorCall(pair).generating(service.provider, service.algorithm, null).let { keys -> { keys(); Unit } } }
        return mapOf("forward" to ResetRun.ofGenerator(CallOrder(emptyList(), make, listOf(generate))))
    }

    private val PAIR = ServiceKey.fold("KeyPairGenerator")
}
