package io.github.junekim0007.cryptobench.config.global

import io.github.junekim0007.cryptobench.config.global.dto.ThermalGate
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.boolean
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.expectKeys
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.optional
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.optionalNumber
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.optionalStrings

object ThermalGateDocument {

    private const val ENABLED = "enabled"
    private const val SENSORS = "sensors"
    private const val MARGIN = "marginCelsius"
    private const val POLL = "pollSeconds"
    private const val TIMEOUT = "timeoutSeconds"

    fun of(gate: ThermalGate): Map<String, Any> = linkedMapOf(
        ENABLED to gate.enabled, SENSORS to gate.sensors, MARGIN to gate.marginCelsius, POLL to gate.pollSeconds, TIMEOUT to gate.timeoutSeconds)

    fun parse(document: Map<String, Any>, path: String): ThermalGate {
        expectKeys(document, listOf(ENABLED, SENSORS, MARGIN, POLL, TIMEOUT), path)
        return ThermalGate(
            enabled = optional(document, ENABLED, true, ::boolean),
            sensors = optionalStrings(document, SENSORS),
            marginCelsius = optionalNumber(document, MARGIN)?.toDouble() ?: ThermalGate.MARGIN_CELSIUS,
            pollSeconds = optionalNumber(document, POLL)?.toInt() ?: ThermalGate.POLL_SECONDS,
            timeoutSeconds = optionalNumber(document, TIMEOUT)?.toInt() ?: ThermalGate.TIMEOUT_SECONDS,
        )
    }
}
