package io.github.junekim0007.cryptobench.discovery.query

import io.github.junekim0007.cryptobench.discovery.contract.CapturedEnvironment
import io.github.junekim0007.cryptobench.discovery.contract.ProviderEntry
import io.github.junekim0007.cryptobench.discovery.contract.ServiceEntry

class CaptureQuery(private val capture: CapturedEnvironment) {

    private val providersByPrecedence: List<ProviderEntry> = capture.providers.sortedBy { it.precedence }

    private val indexByProvider: Map<String, ServiceIndex> =
        capture.providers.associate { it.name to ServiceIndex(it) }

    fun whoServes(type: String, algorithmOrAlias: String): List<ProviderEntry> =
        providersByPrecedence.filter { indexByProvider.getValue(it.name).find(type, algorithmOrAlias) != null }

    fun serviceOf(providerName: String, type: String, algorithmOrAlias: String): ServiceEntry? =
        indexByProvider[providerName]?.find(type, algorithmOrAlias)

    fun namesOf(type: String, algorithmOrAlias: String): Set<String> =
        whoServes(type, algorithmOrAlias)
            .mapNotNull { indexByProvider.getValue(it.name).find(type, algorithmOrAlias) }
            .flatMapTo(LinkedHashSet()) { listOf(it.algorithm) + it.aliases }

    fun onlyOn(providerName: String): List<ServiceEntry> {
        val provider = capture.providers.firstOrNull { it.name == providerName } ?: return emptyList()
        return provider.services.filter { service -> whoServes(service.type, service.algorithm).size == 1 }
    }

    fun tree(): Map<String, Map<String, ServiceShape>> = ServiceTree.of(providersByPrecedence)
}
