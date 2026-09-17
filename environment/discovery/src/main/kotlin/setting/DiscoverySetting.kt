package io.github.junekim0007.cryptobench.discovery.setting

import io.github.junekim0007.cryptobench.discovery.contract.ServiceKey

import java.util.SortedSet

/**
 * What the benchmark needs from a capture: which in-scope services each provider answers, plus the
 * attributes that narrow the matrix. Built by [DiscoverySettingConverter], never from the JCA.
 */
data class DiscoverySetting(
    val device: Device,
    val providers: List<ProviderSetting> = emptyList(),
    val capturedAtMillis: Long = 0L,
    val schemaVersion: Int = SCHEMA_VERSION,
) {

    /** Providers that answer this type and algorithm or alias, in search order. */
    fun providersFor(type: String, algorithmOrAlias: String): List<ProviderSetting> =
        providers.filter { it.find(type, algorithmOrAlias) != null }

    /** Canonical algorithm names registered for a type, across every provider. */
    fun algorithms(type: String): SortedSet<String> {
        val wanted = ServiceKey.fold(type)
        return providers
            .flatMap { it.services }
            .filter { ServiceKey.fold(it.type) == wanted }
            .mapTo(sortedSetOf()) { it.algorithm }
    }

    /** The device a setting describes. */
    data class Device(
        val model: String = "",
        val manufacturer: String = "",
        val hardware: String = "",
        val sdkInt: Int = 0,
        val release: String = "",
    )

    /** One provider, reduced to its in-scope services. */
    data class ProviderSetting(
        val name: String,
        val precedence: Int,
        val version: String = "",
        val services: List<ServiceSetting> = emptyList(),
    ) {

        private val byNameOrAlias: Map<ServiceKey, ServiceSetting> =
            HashMap<ServiceKey, ServiceSetting>().apply {
                for (service in services) {
                    put(ServiceKey(service.type, service.algorithm), service)
                    for (alias in service.aliases) {
                        put(ServiceKey(service.type, alias), service)
                    }
                }
            }

        /** True when at least one in-scope service remains after conversion. */
        val usable: Boolean get() = services.isNotEmpty()

        /** The service answering this type and algorithm or alias, or null. Case-insensitive. */
        fun find(type: String, algorithmOrAlias: String): ServiceSetting? =
            byNameOrAlias[ServiceKey(type, algorithmOrAlias)]
    }

    /** One in-scope service with the attributes that narrow the benchmark matrix. */
    data class ServiceSetting(
        val type: String,
        val algorithm: String,
        val aliases: List<String> = emptyList(),
        /** Empty when the provider does not declare it, not when it supports none. */
        val supportedModes: List<String> = emptyList(),
        /** Empty when the provider does not declare it, not when it supports none. */
        val supportedPaddings: List<String> = emptyList(),
        /** Largest declared key size, or null when undeclared. */
        val keySize: Int? = null,
    )

    companion object {
        const val SCHEMA_VERSION = 1
    }
}
