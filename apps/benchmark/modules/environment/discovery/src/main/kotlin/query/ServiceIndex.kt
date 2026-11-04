package io.github.junekim0007.cryptobench.discovery.query

import io.github.junekim0007.cryptobench.discovery.contract.ProviderEntry
import io.github.junekim0007.cryptobench.discovery.contract.ServiceEntry
import io.github.junekim0007.cryptobench.discovery.contract.ServiceKey

internal class ServiceIndex(provider: ProviderEntry) {

    private val byNameOrAlias: Map<ServiceKey, ServiceEntry> = HashMap<ServiceKey, ServiceEntry>().apply {
        for (service in provider.services) {
            put(ServiceKey(service.type, service.algorithm), service)
            for (alias in service.aliases) {
                put(ServiceKey(service.type, alias), service)
            }
        }
    }

    fun find(type: String, algorithmOrAlias: String): ServiceEntry? =
        byNameOrAlias[ServiceKey(type, algorithmOrAlias)]
}
