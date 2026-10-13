package io.github.junekim0007.cryptobench.preparation.global

import io.github.junekim0007.cryptobench.preparation.shared.DocumentFields.expectKeys
import io.github.junekim0007.cryptobench.preparation.shared.DocumentFields.number
import io.github.junekim0007.cryptobench.preparation.shared.DocumentFields.string

object EnergyReader {

    private const val CAPTURE = "capture"
    private const val WINDOW_SECONDS = "windowSeconds"
    private const val WARMUP_SECONDS = "warmupSeconds"
    private const val COOLDOWN_SECONDS = "cooldownSeconds"

    fun read(document: Map<String, Any>, path: String): EnergySettings {
        expectKeys(document, listOf(CAPTURE, WINDOW_SECONDS, WARMUP_SECONDS, COOLDOWN_SECONDS), path)
        return try {
            EnergySettings(
                capture = document[CAPTURE]?.let { string(document, CAPTURE) },
                windowSeconds = document[WINDOW_SECONDS]?.let { number(document, WINDOW_SECONDS).toInt() },
                warmupSeconds = document[WARMUP_SECONDS]?.let { number(document, WARMUP_SECONDS).toInt() },
                cooldownSeconds = document[COOLDOWN_SECONDS]?.let { number(document, COOLDOWN_SECONDS).toInt() },
            )
        } catch (failure: IllegalArgumentException) {
            throw IllegalArgumentException("${failure.message} at $path", failure)
        }
    }
}
