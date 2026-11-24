package io.github.junekim0007.cryptobench.config.source

import io.github.junekim0007.cryptobench.contract.capture.CapturedEnvironment
import io.github.junekim0007.cryptobench.contract.capture.RuntimeDocument
import io.github.junekim0007.cryptobench.document.names.CaptureSpellings

data class CaptureView(
    val device: Map<String, Any>,
    val providers: List<String>,
    val spellings: CaptureSpellings = CaptureSpellings.NONE,
) {

    companion object {
        fun of(capture: CapturedEnvironment): CaptureView = CaptureView(
            device = RuntimeDocument.of(capture.runtime),
            providers = capture.providers.map { it.name },
            spellings = CaptureSpellings(capture.providers.associate { provider ->
                provider.name to provider.services.filter { it.aliases.isNotEmpty() }.map { CaptureSpellings.Service(it.type, it.algorithm, it.aliases) }
            }),
        )
    }
}
