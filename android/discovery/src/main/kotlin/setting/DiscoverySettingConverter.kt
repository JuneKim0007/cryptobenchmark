package io.github.junekim0007.cryptobench.discovery.setting

import io.github.junekim0007.cryptobench.discovery.ServiceKey
import io.github.junekim0007.cryptobench.discovery.capture.CapturedEnvironment
import io.github.junekim0007.cryptobench.discovery.capture.ServiceEntry

/**
 * Reduces a full capture to the discovery setting. Typed to typed: it never reads a file or a field
 * name, so serialization changes cannot break it. Every field it drops is listed in
 * security_contract.md under "cropped".
 */
class DiscoverySettingConverter(types: Collection<String> = BENCHMARKED_TYPES) {

    /** Scope is a parameter so it can come from configuration rather than the constant. */
    private val types: Set<String> = types.mapTo(HashSet()) { ServiceKey.fold(it) }

    fun convert(capture: CapturedEnvironment): DiscoverySetting = DiscoverySetting(
        device = DiscoverySetting.Device(
            model = capture.runtime.model,
            manufacturer = capture.runtime.manufacturer,
            hardware = capture.runtime.hardware,
            sdkInt = capture.runtime.sdkInt,
            release = capture.runtime.release,
        ),
        providers = capture.providers
            .map { provider ->
                DiscoverySetting.ProviderSetting(
                    name = provider.name,
                    precedence = provider.precedence,
                    version = provider.version,
                    services = inScope(provider.services),
                )
            }
            .sortedBy { it.precedence },
        capturedAtMillis = capture.capturedAtMillis,
    )

    private fun inScope(services: List<ServiceEntry>): List<DiscoverySetting.ServiceSetting> =
        services
            .filter { ServiceKey.fold(it.type) in types }
            .map { service ->
                DiscoverySetting.ServiceSetting(
                    type = service.type,
                    algorithm = service.algorithm,
                    aliases = service.aliases,
                    supportedModes = service.attributes.supportedModes,
                    supportedPaddings = service.attributes.supportedPaddings,
                    keySize = service.attributes.keySize,
                )
            }

    companion object {

        /** Service types the benchmark measures. Everything else in a capture is cropped. */
        val BENCHMARKED_TYPES: Set<String> = linkedSetOf(
            "Cipher", "MessageDigest", "Mac", "Signature",
            "KeyGenerator", "KeyPairGenerator", "KeyAgreement",
        )
    }
}
