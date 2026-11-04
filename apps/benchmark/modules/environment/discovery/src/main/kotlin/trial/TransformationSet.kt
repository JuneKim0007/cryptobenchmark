package io.github.junekim0007.cryptobench.discovery.trial

import io.github.junekim0007.cryptobench.discovery.contract.ServiceEntry

internal object TransformationSet {

    fun of(service: ServiceEntry): List<String> {
        val modes = service.attributes.supportedModes
        val paddings = service.attributes.supportedPaddings
        val composed = modes.flatMap { mode -> paddings.map { padding -> service.algorithm + "/" + mode + "/" + padding } }
        return listOf(service.algorithm) + composed
    }
}
