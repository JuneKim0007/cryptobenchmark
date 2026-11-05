package io.github.junekim0007.cryptobench.discovery.trial.requirement

import io.github.junekim0007.cryptobench.discovery.contract.ServiceRequirement

// A provider that ran no key at all, refusing every software key and generating none without its own spec, holds its keys inside.
internal object KeyOrigin {

    private val REFUSALS = setOf(ServiceRequirement.KEY_REFUSED, ServiceRequirement.GENERATION_REFUSED, ServiceRequirement.NO_KEY)

    private const val FACTORY = "SECRETKEYFACTORY"

    private val KEY_TYPES = setOf("CIPHER", "SIGNATURE", "MAC", "KEYAGREEMENT", "KEYGENERATOR", "KEYPAIRGENERATOR")

    fun applied(services: List<ServiceRequirement>): List<ServiceRequirement> {
        val bound = services.groupBy { it.provider }.filterValues { ofProvider ->
            val keyed = ofProvider.filter { it.type.uppercase() in KEY_TYPES }
            keyed.isNotEmpty() && keyed.none { it.status == ServiceRequirement.RUNNABLE } && keyed.any { it.reason in REFUSALS }
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
