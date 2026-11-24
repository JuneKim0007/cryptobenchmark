package io.github.junekim0007.cryptobench.discovery.trial.requirement

import io.github.junekim0007.cryptobench.contract.requirements.ServiceRequirement
import io.github.junekim0007.cryptobench.discovery.trial.call.EngineTypes
import io.github.junekim0007.cryptobench.document.names.AlgorithmNames

// A provider with no generator or factory of its own that runs, refusing some key, holds its keys inside; the relabel keeps what the call measured.
internal object KeyOrigin {

    private val REFUSALS = setOf(ServiceRequirement.KEY_REFUSED, ServiceRequirement.GENERATION_REFUSED, ServiceRequirement.NO_KEY)

    fun applied(services: List<ServiceRequirement>): List<ServiceRequirement> {
        val bound = services.groupBy { it.provider }.filterValues { ofProvider ->
            ofProvider.none { AlgorithmNames.fold(it.type) in EngineTypes.KEY_MAKERS && it.status == ServiceRequirement.RUNNABLE } && ofProvider.any { it.reason in REFUSALS }
        }.keys
        return services.map { service ->
            if (service.provider in bound && (service.reason in REFUSALS || AlgorithmNames.fold(service.type) == EngineTypes.FACTORY && service.status == ServiceRequirement.NOT_RUNNABLE)) {
                service.copy(reason = ServiceRequirement.KEYSTORE_BORN_KEY, measuredReason = service.reason, conditions = service.conditions + ServiceRequirement.KEYSTORE_BORN_CONDITION)
            } else {
                service
            }
        }
    }
}
