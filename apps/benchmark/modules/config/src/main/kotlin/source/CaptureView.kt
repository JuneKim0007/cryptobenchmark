package io.github.junekim0007.cryptobench.config.source

import java.util.Locale

data class CaptureView(
    val capturedAtMillis: Long,
    val device: Map<String, Any>,
    val providers: List<String>,
    // provider -> (type, registered name folded) -> the aliases the capture lists for that service
    val aliases: Map<String, Map<Pair<String, String>, List<String>>> = emptyMap(),
) {

    fun aliasesOf(provider: String, type: String, name: String): List<String> =
        aliases[provider]?.get(service(type, name)).orEmpty()

    companion object {
        fun service(type: String, name: String): Pair<String, String> = type to name.uppercase(Locale.ROOT)
    }
}
