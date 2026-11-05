package io.github.junekim0007.cryptobench.discovery.adapter

import io.github.junekim0007.cryptobench.discovery.bundled.InstalledProvider
import io.github.junekim0007.cryptobench.discovery.contract.CapturedEnvironment
import io.github.junekim0007.cryptobench.discovery.contract.ProviderEntry
import io.github.junekim0007.cryptobench.discovery.contract.ProviderOrigin
import io.github.junekim0007.cryptobench.discovery.contract.RuntimeInfo
import io.github.junekim0007.cryptobench.discovery.contract.ServiceAttributes
import io.github.junekim0007.cryptobench.discovery.contract.ServiceEntry
import io.github.junekim0007.cryptobench.discovery.contract.ServiceKey
import java.security.Provider

class ProviderProbe {

    fun capture(
        providers: Array<Provider>?,
        runtime: RuntimeInfo = DeviceRuntimeReader.read(),
        capturedAtMillis: Long = System.currentTimeMillis(),
        bundled: List<InstalledProvider> = emptyList(),
    ): CapturedEnvironment {
        val artifacts = bundled.associate { it.name to it.artifact }
        return CapturedEnvironment(
            runtime = runtime,
            providers = providers?.mapIndexed { index, provider -> toEntry(provider, index + 1, artifacts[provider.name]) }.orEmpty(),
            capturedAtMillis = capturedAtMillis,
            deviceClockMillis = System.currentTimeMillis(),
        )
    }

    private fun toEntry(provider: Provider, precedence: Int, artifact: String?): ProviderEntry {
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

        return ProviderEntry(
            name = provider.name,
            precedence = precedence,
            version = index.version,
            services = services,
            origin = if (artifact == null) ProviderOrigin.PLATFORM else ProviderOrigin.BUNDLED,
            artifact = artifact.orEmpty(),
        )
    }
}
