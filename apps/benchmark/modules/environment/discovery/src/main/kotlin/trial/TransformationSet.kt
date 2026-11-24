package io.github.junekim0007.cryptobench.discovery.trial

import io.github.junekim0007.cryptobench.contract.capture.CapturedEnvironment
import io.github.junekim0007.cryptobench.contract.capture.ProviderEntry
import io.github.junekim0007.cryptobench.contract.capture.ServiceEntry
import io.github.junekim0007.cryptobench.document.names.AlgorithmNames

internal class TransformationSet(capture: CapturedEnvironment) {

    // every alg/mode/padding a captured provider registers, by folded base; the first spelling in capture order
    private val named: Map<String, List<String>> = capture.providers.flatMap { it.services }.filter(::isCipher)
        .map { it.algorithm }.filter { it.split('/').size == PARTS }
        .distinctBy(AlgorithmNames::fold)
        .groupBy { AlgorithmNames.fold(it.substringBefore('/')) }

    private val owned = HashMap<String, Set<String>>()

    // a service declaring neither modes nor paddings tries what other providers register for its base, but no name its own provider registers
    fun of(provider: ProviderEntry, service: ServiceEntry): List<String> {
        if (service.attributes.supportedModes.isNotEmpty() || service.attributes.supportedPaddings.isNotEmpty()) {
            return declared(service)
        }
        val own = owned.getOrPut(provider.name) { provider.services.filter(::isCipher).flatMap { listOf(it.algorithm) + it.aliases }.map(AlgorithmNames::fold).toSet() }
        return named[AlgorithmNames.fold(service.algorithm)].orEmpty().filter { AlgorithmNames.fold(it) !in own }
    }

    companion object {
        private const val PARTS = 3

        fun isCipher(service: ServiceEntry): Boolean = AlgorithmNames.fold(service.type) == EngineTypes.CIPHER

        private fun declared(service: ServiceEntry): List<String> =
            service.attributes.supportedModes.flatMap { mode -> service.attributes.supportedPaddings.map { padding -> service.algorithm + "/" + mode + "/" + padding } }
    }
}
