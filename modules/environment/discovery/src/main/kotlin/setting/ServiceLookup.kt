package io.github.junekim0007.cryptobench.discovery.setting

import io.github.junekim0007.cryptobench.discovery.contract.ServiceKey

internal class ServiceLookup(services: List<ServiceSetting>) {

    private val byNameOrAlias: Map<ServiceKey, ServiceSetting> = HashMap<ServiceKey, ServiceSetting>().apply {
        for (service in services) {
            put(ServiceKey(service.type, service.algorithm), service)
            for (alias in service.aliases) {
                put(ServiceKey(service.type, alias), service)
            }
        }
    }

    fun find(type: String, algorithmOrAlias: String): ServiceSetting? =
        byNameOrAlias[ServiceKey(type, algorithmOrAlias)]
}
