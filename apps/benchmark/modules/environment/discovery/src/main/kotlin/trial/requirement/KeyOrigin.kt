package io.github.junekim0007.cryptobench.discovery.trial.requirement

import io.github.junekim0007.cryptobench.discovery.contract.ServiceRequirement

// A provider with no generator or factory of its own that runs, refusing some key, holds its keys inside.
internal object KeyOrigin {

    private val REFUSALS = setOf(ServiceRequirement.KEY_REFUSED, ServiceRequirement.GENERATION_REFUSED, ServiceRequirement.NO_KEY)

    private const val FACTORY = "SECRETKEYFACTORY"

    private val KEY_MAKERS = setOf("KEYGENERATOR", "KEYPAIRGENERATOR", FACTORY)

    fun applied(services: List<ServiceRequirement>): List<ServiceRequirement> {
        val bound = services.groupBy { it.provider }.filterValues { ofProvider ->
            ofProvider.none { it.type.uppercase() in KEY_MAKERS && it.status == ServiceRequirement.RUNNABLE } && ofProvider.any { it.reason in REFUSALS }
        }.keys
        return services.map { service ->
            if (service.provider in bound && (service.reason in REFUSALS || service.type.uppercase() == FACTORY && service.status == ServiceRequirement.NOT_RUNNABLE)) {
                service.copy(reason = ServiceRequirement.KEYSTORE_BORN_KEY, conditions = service.conditions + ServiceRequirement.KEYSTORE_BORN_CONDITION)
            } else {
                service
            }
        }
    }
}
