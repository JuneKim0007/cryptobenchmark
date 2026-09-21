package io.github.junekim0007.cryptobench.discovery.adapter

import io.github.junekim0007.cryptobench.discovery.contract.AliasEntry
import io.github.junekim0007.cryptobench.discovery.contract.CapturedEnvironment
import io.github.junekim0007.cryptobench.discovery.contract.ProviderEntry
import io.github.junekim0007.cryptobench.discovery.contract.RuntimeInfo
import io.github.junekim0007.cryptobench.discovery.contract.ServiceAttributes
import io.github.junekim0007.cryptobench.discovery.contract.ServiceEntry
import io.github.junekim0007.cryptobench.discovery.contract.ServiceKey
import java.security.Provider

class ProviderProbe {

    fun capture(
        providers: Array<Provider>?,
        runtime: RuntimeInfo = RuntimeInfo.unknown(),
        capturedAtMillis: Long = System.currentTimeMillis(),
    ): CapturedEnvironment = CapturedEnvironment(
        runtime = runtime,
        providers = providers?.mapIndexed { index, provider -> toEntry(provider, index + 1) }.orEmpty(),
        capturedAtMillis = capturedAtMillis,
    )

    private fun toEntry(provider: Provider, precedence: Int): ProviderEntry {
        val index = PropertyMapIndex.of(provider)

        val services = provider.services.orEmpty().map { service ->
            val serviceKey = ServiceKey(service.type, service.algorithm)
            ServiceEntry(
                type = service.type,
                algorithm = service.algorithm,
                className = service.className ?: "",
                aliases = index.aliasesByTarget[serviceKey]?.sorted().orEmpty(),
                attributes = ServiceAttributes.of(index.attributesByService[serviceKey]),
            )
        }.sortedWith(compareBy({ it.type }, { it.algorithm }))

        val present = services.mapTo(HashSet()) { ServiceKey(it.type, it.algorithm) }

        return ProviderEntry(
            name = provider.name,
            precedence = precedence,
            version = provider.versionStr,
            info = provider.info ?: "",
            services = services,
            unresolvedAliases = index.aliases
                .filterNot { it.targetKey in present }
                .map { AliasEntry(it.type, it.name, it.target) }
                .sortedWith(compareBy({ it.type }, { it.name })),
        )
    }
}
