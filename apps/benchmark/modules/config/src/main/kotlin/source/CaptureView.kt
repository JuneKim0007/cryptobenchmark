package io.github.junekim0007.cryptobench.config.source

import io.github.junekim0007.cryptobench.contract.capture.CapturedEnvironment
import io.github.junekim0007.cryptobench.contract.capture.RuntimeDocument
import java.util.Locale

data class CaptureView(
    val device: Map<String, Any>,
    val providers: List<String>,
    // provider -> (type, registered name folded) -> the aliases the capture lists for that service
    val aliases: Map<String, Map<Pair<String, String>, List<String>>> = emptyMap(),
) {

    fun aliasesOf(provider: String, type: String, name: String): List<String> =
        aliases[provider]?.get(service(type, name)).orEmpty()

    companion object {
        fun service(type: String, name: String): Pair<String, String> = type to name.uppercase(Locale.ROOT)

        fun of(capture: CapturedEnvironment): CaptureView = CaptureView(
            device = RuntimeDocument.of(capture.runtime),
            providers = capture.providers.map { it.name },
            aliases = capture.providers.associate { provider ->
                provider.name to provider.services.filter { it.aliases.isNotEmpty() }.associate { service(it.type, it.algorithm) to it.aliases }
            },
        )
    }
}
