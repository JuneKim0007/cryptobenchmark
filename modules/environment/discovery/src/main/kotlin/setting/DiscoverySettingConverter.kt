package io.github.junekim0007.cryptobench.discovery.setting

import io.github.junekim0007.cryptobench.discovery.contract.CapturedEnvironment
import io.github.junekim0007.cryptobench.discovery.contract.ServiceEntry
import io.github.junekim0007.cryptobench.discovery.contract.ServiceKey

class DiscoverySettingConverter(types: Collection<String> = BenchmarkScope.TYPES) {

    private val types: Set<String> = types.mapTo(HashSet()) { ServiceKey.fold(it) }

    fun convert(capture: CapturedEnvironment): DiscoverySetting = DiscoverySetting(
        device = Device(
            model = capture.runtime.model,
            manufacturer = capture.runtime.manufacturer,
            hardware = capture.runtime.hardware,
            sdkInt = capture.runtime.sdkInt,
            release = capture.runtime.release,
        ),
        providers = capture.providers
            .map { provider ->
                ProviderSetting(
                    name = provider.name,
                    precedence = provider.precedence,
                    version = provider.version,
                    services = inScope(provider.services),
                )
            }
            .sortedBy { it.precedence },
        capturedAtMillis = capture.capturedAtMillis,
    )

    private fun inScope(services: List<ServiceEntry>): List<ServiceSetting> =
        services
            .filter { ServiceKey.fold(it.type) in types }
            .map { service ->
                ServiceSetting(
                    type = service.type,
                    algorithm = service.algorithm,
                    aliases = service.aliases,
                    supportedModes = service.attributes.supportedModes,
                    supportedPaddings = service.attributes.supportedPaddings,
                    keySize = service.attributes.keySize,
                )
            }
}
