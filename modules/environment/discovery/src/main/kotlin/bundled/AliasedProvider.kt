package io.github.junekim0007.cryptobench.discovery.bundled

import java.security.Provider

// Services are re-bound to this provider so an instance reports the alias, not the clashing name.
@Suppress("DEPRECATION")
class AliasedProvider(name: String, private val delegate: Provider) : Provider(name, delegate.version, delegate.info) {

    init {
        for (key in delegate.stringPropertyNames()) {
            if (!key.startsWith(IDENTITY)) put(key, delegate.getProperty(key))
        }
    }

    override fun getService(type: String, algorithm: String): Service? = delegate.getService(type, algorithm)?.let(::rebound)

    override fun getServices(): Set<Service> = delegate.services.mapTo(LinkedHashSet(), ::rebound)

    private fun rebound(service: Service): Service = Rebound(this, service, attributesOf(service))

    private fun attributesOf(service: Service): Map<String, String> {
        val prefix = "${service.type}.${service.algorithm} "
        return delegate.stringPropertyNames().filter { it.startsWith(prefix, ignoreCase = true) }
            .associate { it.substring(prefix.length) to delegate.getProperty(it) }
    }

    private class Rebound(provider: Provider, private val target: Service, attributes: Map<String, String>) :
        Service(provider, target.type, target.algorithm, target.className, null, attributes) {

        override fun newInstance(constructorParameter: Any?): Any = target.newInstance(constructorParameter)

        override fun supportsParameter(parameter: Any?): Boolean = target.supportsParameter(parameter)
    }

    private companion object {
        const val IDENTITY = "Provider.id"
    }
}
