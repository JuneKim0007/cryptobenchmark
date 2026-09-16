package io.github.junekim0007.cryptobench.discovery.probe

import io.github.junekim0007.cryptobench.discovery.ServiceKey
import io.github.junekim0007.cryptobench.discovery.capture.CapturedEnvironment
import io.github.junekim0007.cryptobench.discovery.capture.ProviderEntry
import io.github.junekim0007.cryptobench.discovery.capture.RuntimeInfo
import io.github.junekim0007.cryptobench.discovery.capture.ServiceAttributes
import io.github.junekim0007.cryptobench.discovery.capture.ServiceEntry

import java.security.Provider

/**
 * Reads the JCA into a capture. The caller passes the providers, so this never calls Security and
 * can be driven with hand-built providers. Null and ordering are normalised here, which lets the
 * capture model stay plain data.
 */
class ProviderProbe {

    private data class Alias(val type: String, val name: String, val target: String) {
        val targetKey: ServiceKey get() = ServiceKey.of(type, target)
    }

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
        val aliases = mutableListOf<Alias>()
        val attributes = mutableMapOf<ServiceKey, MutableMap<String, Any>>()
        index(provider, aliases, attributes)

        val aliasesByTarget = aliases.groupBy({ it.targetKey }, { it.name })

        val services = provider.services.orEmpty().map { service ->
            val serviceKey = ServiceKey.of(service.type, service.algorithm)
            ServiceEntry(
                type = service.type,
                algorithm = service.algorithm,
                className = service.className ?: "",
                aliases = aliasesByTarget[serviceKey]?.sorted().orEmpty(),
                attributes = ServiceAttributes.of(attributes[serviceKey]),
            )
        }.sortedWith(compareBy({ it.type }, { it.algorithm }))

        val present = services.mapTo(HashSet()) { it.key }

        return ProviderEntry(
            name = provider.name,
            precedence = precedence,
            version = provider.version.toString(),
            info = provider.info ?: "",
            services = services,
            unresolvedAliases = aliases
                .filterNot { it.targetKey in present }
                .associate { "${it.type} ${it.name}" to it.target }
                .toSortedMap(),
        )
    }

    private fun index(
        provider: Provider,
        aliases: MutableList<Alias>,
        attributes: MutableMap<ServiceKey, MutableMap<String, Any>>,
    ) {
        for (raw in provider.stringPropertyNames()) {
            val value = provider.getProperty(raw) ?: continue
            when (val propertyKey = PropertyKey.classify(raw)) {
                is PropertyKey.Alias ->
                    aliases += Alias(propertyKey.type, propertyKey.name, value)
                is PropertyKey.Attribute ->
                    attributes.getOrPut(propertyKey.serviceKey) { mutableMapOf() }[propertyKey.name] =
                        parseOrRaw(propertyKey.name, value)
                is PropertyKey.ServiceImpl,
                PropertyKey.ProviderMeta,
                PropertyKey.Malformed -> Unit
            }
        }
    }

    /** Capture records what is there; only an unparseable number is kept raw, for a reader to judge. */
    private fun parseOrRaw(attribute: String, value: String): Any = try {
        AttributeKind.parse(attribute, value)
    } catch (e: NumberFormatException) {
        value
    }
}
