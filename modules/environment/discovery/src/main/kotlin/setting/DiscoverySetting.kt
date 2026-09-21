package io.github.junekim0007.cryptobench.discovery.setting

import io.github.junekim0007.cryptobench.discovery.contract.ServiceKey
import java.util.SortedSet

data class DiscoverySetting(
    val device: Device,
    val providers: List<ProviderSetting> = emptyList(),
    val capturedAtMillis: Long = 0L,
    val schemaVersion: Int = SCHEMA_VERSION,
) {

    fun providersFor(type: String, algorithmOrAlias: String): List<ProviderSetting> =
        providers.filter { it.find(type, algorithmOrAlias) != null }

    fun algorithms(type: String): SortedSet<String> {
        val wanted = ServiceKey.fold(type)
        return providers
            .flatMap { it.services }
            .filter { ServiceKey.fold(it.type) == wanted }
            .mapTo(sortedSetOf()) { it.algorithm }
    }

    companion object {
        const val SCHEMA_VERSION = 1
    }
}
