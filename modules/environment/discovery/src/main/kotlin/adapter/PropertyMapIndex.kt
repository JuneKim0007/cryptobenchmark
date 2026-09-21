package io.github.junekim0007.cryptobench.discovery.adapter

import io.github.junekim0007.cryptobench.discovery.contract.ServiceKey
import java.security.Provider

internal class PropertyMapIndex private constructor(
    val meta: Map<String, String>,
    val aliases: List<DeclaredAlias>,
    val attributesByService: Map<ServiceKey, Map<String, Any>>,
) {

    val version: String get() = meta[VERSION_FIELD] ?: ""

    val aliasesByTarget: Map<ServiceKey, List<String>> =
        aliases.groupBy({ it.targetKey }, { it.name })

    companion object {

        const val VERSION_FIELD = "id version"

        fun of(provider: Provider): PropertyMapIndex {
            val meta = mutableMapOf<String, String>()
            val aliases = mutableListOf<DeclaredAlias>()
            val attributes = mutableMapOf<ServiceKey, MutableMap<String, Any>>()
            for (raw in provider.stringPropertyNames()) {
                val value = provider.getProperty(raw)?.takeIf { it.isNotBlank() } ?: continue
                when (val propertyKey = PropertyKeyParser.classify(raw)) {
                    is PropertyKey.ProviderMeta ->
                        meta[propertyKey.field] = value
                    is PropertyKey.Alias ->
                        aliases += DeclaredAlias(propertyKey.type, propertyKey.name, value)
                    is PropertyKey.Attribute ->
                        attributes.getOrPut(ServiceKey(propertyKey.type, propertyKey.algorithm)) { mutableMapOf() }[propertyKey.name] =
                            AttributeValueParser.parseOrRaw(propertyKey.name, value)
                    is PropertyKey.ServiceImpl,
                    PropertyKey.Malformed -> Unit
                }
            }
            return PropertyMapIndex(meta, aliases, attributes)
        }
    }
}
