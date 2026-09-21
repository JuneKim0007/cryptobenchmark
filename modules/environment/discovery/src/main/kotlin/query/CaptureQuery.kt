package io.github.junekim0007.cryptobench.discovery.query

import io.github.junekim0007.cryptobench.discovery.contract.CapturedEnvironment
import io.github.junekim0007.cryptobench.discovery.contract.ProviderEntry
import io.github.junekim0007.cryptobench.discovery.contract.ServiceEntry

/** Questions asked of one capture. Pure: no JCA call, no output, the same answer every time. */
class CaptureQuery(private val capture: CapturedEnvironment) {

    private val providersByPrecedence: List<ProviderEntry> = capture.providers.sortedBy { it.precedence }

    private val indexByProvider: Map<String, ServiceIndex> =
        capture.providers.associate { it.name to ServiceIndex(it) }

    /** Providers that register the service, head first: the head is what an unqualified getInstance returns. */
    fun whoServes(type: String, algorithmOrAlias: String): List<ProviderEntry> =
        providersByPrecedence.filter { indexByProvider.getValue(it.name).find(type, algorithmOrAlias) != null }

    /** Every name that reaches the service, across providers: the registered name and all aliases. */
    fun namesOf(type: String, algorithmOrAlias: String): Set<String> =
        whoServes(type, algorithmOrAlias)
            .mapNotNull { indexByProvider.getValue(it.name).find(type, algorithmOrAlias) }
            .flatMapTo(LinkedHashSet()) { listOf(it.algorithm) + it.aliases }

    /** Services no other provider registers under that name or any alias. */
    fun onlyOn(providerName: String): List<ServiceEntry> {
        val provider = capture.providers.firstOrNull { it.name == providerName } ?: return emptyList()
        return provider.services.filter { service -> whoServes(service.type, service.algorithm).size == 1 }
    }

    /** Engine type → registered algorithm → shape; keys sorted, spelled as first registered. */
    fun tree(): Map<String, Map<String, ServiceShape>> = ServiceTree.of(providersByPrecedence)
}
