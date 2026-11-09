package io.github.junekim0007.cryptobench.config.global

import io.github.junekim0007.cryptobench.config.global.dto.StartMargin
import io.github.junekim0007.cryptobench.config.global.dto.ThermalGate
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.boolean
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.expectKeys
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.optional
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.optionalNumber
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.optionalString

object ThermalGateDocument {

    private const val KEPT = "temperatureKeptCelsius"
    private const val COOLDOWN = "cooldownMinutes"
    private const val POLL = "pollMinutes"
    private const val TERMINATE = "pollTerminateMinutes"
    private const val DISCARD_LIMIT = "discardLimit"
    private const val ON_DISCARD_LIMIT = "onDiscardLimit"
    private const val READ_RETRIES = "readRetries"
    private const val READ_RETRY_SECONDS = "readRetrySeconds"
    private const val START_MARGIN = "startMargin"
    private const val DYNAMIC = "dynamic"
    private const val INITIAL = "initialCelsius"
    private const val FACTOR = "backoffFactor"
    private const val MAXIMUM = "maximumCelsius"
    private const val CLEAN_RUNS = "cleanRunsToRecover"
    private const val RECOVERY = "recoveryCelsius"

    fun of(gate: ThermalGate): Map<String, Any> = linkedMapOf(
        KEPT to gate.temperatureKeptCelsius, COOLDOWN to gate.cooldownMinutes, POLL to gate.pollMinutes, TERMINATE to gate.pollTerminateMinutes,
        DISCARD_LIMIT to gate.discardLimit, ON_DISCARD_LIMIT to gate.onDiscardLimit, READ_RETRIES to gate.readRetries, READ_RETRY_SECONDS to gate.readRetrySeconds,
        START_MARGIN to linkedMapOf<String, Any>(
            DYNAMIC to gate.startMargin.dynamic, INITIAL to gate.startMargin.initialCelsius, FACTOR to gate.startMargin.backoffFactor,
            MAXIMUM to gate.startMargin.maximumCelsius, CLEAN_RUNS to gate.startMargin.cleanRunsToRecover, RECOVERY to gate.startMargin.recoveryCelsius,
        ),
    )

    fun parse(document: Map<String, Any>, path: String): ThermalGate {
        expectKeys(document, listOf(KEPT, COOLDOWN, POLL, TERMINATE, DISCARD_LIMIT, ON_DISCARD_LIMIT, READ_RETRIES, READ_RETRY_SECONDS, START_MARGIN), path)
        val kept = optionalNumber(document, KEPT)?.toDouble() ?: throw IllegalArgumentException("missing_field: $path.$KEPT")
        return ThermalGate(
            temperatureKeptCelsius = kept,
            cooldownMinutes = whole(document, COOLDOWN, ThermalGate.COOLDOWN_MINUTES, path),
            pollMinutes = whole(document, POLL, ThermalGate.POLL_MINUTES, path),
            pollTerminateMinutes = whole(document, TERMINATE, ThermalGate.POLL_TERMINATE_MINUTES, path),
            discardLimit = whole(document, DISCARD_LIMIT, ThermalGate.DISCARD_LIMIT, path),
            onDiscardLimit = optionalString(document, ON_DISCARD_LIMIT).ifEmpty { ThermalGate.NEXT_CASE },
            readRetries = whole(document, READ_RETRIES, ThermalGate.READ_RETRIES, path),
            readRetrySeconds = whole(document, READ_RETRY_SECONDS, ThermalGate.READ_RETRY_SECONDS, path),
            startMargin = margin(document[START_MARGIN], "$path.$START_MARGIN"),
        )
    }

    @Suppress("UNCHECKED_CAST")
    private fun margin(value: Any?, path: String): StartMargin {
        val document = value as? Map<String, Any> ?: return StartMargin()
        expectKeys(document, listOf(DYNAMIC, INITIAL, FACTOR, MAXIMUM, CLEAN_RUNS, RECOVERY), path)
        val defaults = StartMargin()
        return StartMargin(
            dynamic = optional(document, DYNAMIC, defaults.dynamic, ::boolean),
            initialCelsius = optionalNumber(document, INITIAL)?.toDouble() ?: defaults.initialCelsius,
            backoffFactor = optionalNumber(document, FACTOR)?.toDouble() ?: defaults.backoffFactor,
            maximumCelsius = optionalNumber(document, MAXIMUM)?.toDouble() ?: defaults.maximumCelsius,
            cleanRunsToRecover = whole(document, CLEAN_RUNS, defaults.cleanRunsToRecover, path),
            recoveryCelsius = optionalNumber(document, RECOVERY)?.toDouble() ?: defaults.recoveryCelsius,
        )
    }

    private fun whole(document: Map<String, Any>, key: String, default: Int, path: String): Int {
        val value = optionalNumber(document, key) ?: return default
        require(value.toDouble() == value.toInt().toDouble()) { "not_whole: $path.$key $value" }
        return value.toInt()
    }
}
