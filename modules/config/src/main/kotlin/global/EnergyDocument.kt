package io.github.junekim0007.cryptobench.config.global

import io.github.junekim0007.cryptobench.config.global.dto.EnergySettings
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.expectKeys
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.optionalNumber
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.optionalStringOrNull
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.withPathInFailure

object EnergyDocument {

    private const val CAPTURE = "capture"
    private const val WINDOW_SECONDS = "windowSeconds"
    private const val WARMUP_SECONDS = "warmupSeconds"
    private const val COOLDOWN_SECONDS = "cooldownSeconds"

    private val KEYS = listOf(CAPTURE, WINDOW_SECONDS, WARMUP_SECONDS, COOLDOWN_SECONDS)

    fun of(energy: EnergySettings): Map<String, Any> = LinkedHashMap<String, Any>().apply {
        energy.capture?.let { put(CAPTURE, it) }
        energy.windowSeconds?.let { put(WINDOW_SECONDS, it) }
        energy.warmupSeconds?.let { put(WARMUP_SECONDS, it) }
        energy.cooldownSeconds?.let { put(COOLDOWN_SECONDS, it) }
    }

    fun parse(document: Map<String, Any>, path: String): EnergySettings {
        expectKeys(document, KEYS, path)
        // YAML 1.1 reads an unquoted off/on/yes/no as a boolean; name the cause instead of a bare wrong_type.
        (document[CAPTURE] as? Boolean)?.let {
            throw IllegalArgumentException("invalid: energy.capture $it (YAML reads off/on/yes/no as booleans), write one of ${EnergySettings.CAPTURES} at $path")
        }
        return withPathInFailure(path) {
            EnergySettings(
                capture = optionalStringOrNull(document, CAPTURE),
                windowSeconds = optionalNumber(document, WINDOW_SECONDS)?.toInt(),
                warmupSeconds = optionalNumber(document, WARMUP_SECONDS)?.toInt(),
                cooldownSeconds = optionalNumber(document, COOLDOWN_SECONDS)?.toInt(),
            )
        }
    }
}
