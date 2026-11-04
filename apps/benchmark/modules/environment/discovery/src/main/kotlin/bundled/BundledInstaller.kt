package io.github.junekim0007.cryptobench.discovery.bundled

import java.security.Provider
import java.security.Security

// Always appends: a case names its provider explicitly, so a bundled one never shadows the platform's.
class BundledInstaller(private val factory: ProviderFactory) {

    fun install(bundled: List<BundledProvider>): List<InstalledProvider> = bundled.map { spec ->
        val provider = registered(factory.create(spec), spec)
        if (Security.addProvider(provider) == -1) throw BundledProviderException("bundled_not_installed", "${provider.name} (${spec.artifact})")
        InstalledProvider(provider.name, spec.artifact)
    }

    private fun registered(created: Provider, spec: BundledProvider): Provider {
        val alias = spec.alias
        if (alias == null) {
            if (Security.getProvider(created.name) != null) {
                throw BundledProviderException("bundled_name_taken", "${created.name} is already installed; give ${spec.artifact} an alias")
            }
            return created
        }
        if (Security.getProvider(alias) != null) throw BundledProviderException("bundled_alias_taken", "$alias is already installed (${spec.artifact})")
        return if (alias == created.name) created else AliasedProvider(alias, created)
    }
}
