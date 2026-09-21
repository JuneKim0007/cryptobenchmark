package io.github.junekim0007.cryptobench.discovery.query

import io.github.junekim0007.cryptobench.discovery.contract.ProviderEntry
import io.github.junekim0007.cryptobench.discovery.contract.ServiceEntry
import io.github.junekim0007.cryptobench.discovery.contract.ServiceKey

internal object ServiceTree {

    /** Engine type → registered algorithm → shape; keys sorted, spelled as first registered. */
    fun of(providersByPrecedence: List<ProviderEntry>): Map<String, Map<String, ServiceShape>> {
        val shapes = LinkedHashMap<ServiceKey, MutableShape>()
        for (provider in providersByPrecedence) {
            for (service in provider.services) {
                shapes.getOrPut(ServiceKey(service.type, service.algorithm)) { MutableShape(service.type, service.algorithm) }
                    .add(provider.name, service)
            }
        }
        val tree = sortedMapOf<String, MutableMap<String, ServiceShape>>(String.CASE_INSENSITIVE_ORDER)
        for (shape in shapes.values) {
            tree.getOrPut(shape.type) { sortedMapOf(String.CASE_INSENSITIVE_ORDER) }[shape.algorithm] = shape.frozen()
        }
        return tree
    }

    private class MutableShape(val type: String, val algorithm: String) {

        private val modes = LinkedHashSet<String>()
        private val paddings = LinkedHashSet<String>()
        private val providers = LinkedHashSet<String>()

        fun add(providerName: String, service: ServiceEntry) {
            modes += service.attributes.supportedModes
            paddings += service.attributes.supportedPaddings
            providers += providerName
        }

        fun frozen(): ServiceShape = ServiceShape(modes.toList(), paddings.toList(), providers.toList())
    }
}
