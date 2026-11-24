package io.github.junekim0007.cryptobench.discovery.trial

import io.github.junekim0007.cryptobench.contract.capture.CapturedEnvironment
import io.github.junekim0007.cryptobench.contract.capture.ProviderEntry
import io.github.junekim0007.cryptobench.contract.capture.ServiceEntry
import io.github.junekim0007.cryptobench.discovery.adapter.ServiceKey

internal class TransformationSet(capture: CapturedEnvironment) {

    // every alg/mode/padding a captured provider registers, by folded base; the first spelling in capture order
    private val named: Map<String, List<String>> = capture.providers.flatMap { it.services }.filter(::isCipher)
        .map { it.algorithm }.filter { it.split('/').size == PARTS }
        .distinctBy(ServiceKey::fold)
        .groupBy { ServiceKey.fold(it.substringBefore('/')) }

    private val owned = HashMap<String, Set<String>>()

    // a service declaring neither modes nor paddings tries what other providers register for its base, but no name its own provider registers
    fun of(provider: ProviderEntry, service: ServiceEntry): List<String> {
        if (service.attributes.supportedModes.isNotEmpty() || service.attributes.supportedPaddings.isNotEmpty()) {
            return declared(service)
        }
        val own = owned.getOrPut(provider.name) { provider.services.filter(::isCipher).flatMap { listOf(it.algorithm) + it.aliases }.map(ServiceKey::fold).toSet() }
        return named[ServiceKey.fold(service.algorithm)].orEmpty().filter { ServiceKey.fold(it) !in own }
    }

    companion object {
        private const val PARTS = 3
        private val CIPHER = ServiceKey.fold("Cipher")

        fun isCipher(service: ServiceEntry): Boolean = ServiceKey.fold(service.type) == CIPHER

        private fun declared(service: ServiceEntry): List<String> =
            service.attributes.supportedModes.flatMap { mode -> service.attributes.supportedPaddings.map { padding -> service.algorithm + "/" + mode + "/" + padding } }
    }
}
