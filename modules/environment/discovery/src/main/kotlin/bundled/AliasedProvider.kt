package io.github.junekim0007.cryptobench.discovery.bundled

import java.security.Provider
import java.util.concurrent.ConcurrentHashMap

// Services are re-bound to this provider so an instance reports the alias, not the clashing name.
@Suppress("DEPRECATION")
class AliasedProvider(name: String, private val delegate: Provider) : Provider(name, delegate.version, delegate.info) {

    // JCA looks a service up on every getInstance and every Cipher.init: one Rebound per delegate service, built once
    private val rebounds = ConcurrentHashMap<String, Service>()
    private val attributes: Map<String, Map<String, String>>

    init {
        val names = delegate.stringPropertyNames()
        for (key in names) {
            if (!key.startsWith(IDENTITY)) put(key, delegate.getProperty(key))
        }
        attributes = names.filter { it.indexOf(' ') > 0 }
            .groupBy({ it.substringBefore(' ').lowercase() }, { it.substringAfter(' ') to delegate.getProperty(it) })
            .mapValues { (_, pairs) -> pairs.toMap() }
    }

    override fun getService(type: String, algorithm: String): Service? = delegate.getService(type, algorithm)?.let(::rebound)

    override fun getServices(): Set<Service> = delegate.services.mapTo(LinkedHashSet(), ::rebound)

    private fun rebound(service: Service): Service =
        rebounds.computeIfAbsent(keyOf(service)) { Rebound(this, service, attributes[it].orEmpty()) }

    private fun keyOf(service: Service): String = "${service.type}.${service.algorithm}".lowercase()

    private class Rebound(provider: Provider, private val target: Service, attributes: Map<String, String>) :
        Service(provider, target.type, target.algorithm, target.className, null, attributes) {

        override fun newInstance(constructorParameter: Any?): Any = target.newInstance(constructorParameter)

        override fun supportsParameter(parameter: Any?): Boolean = target.supportsParameter(parameter)
    }

    private companion object {
        const val IDENTITY = "Provider.id"
    }
}
