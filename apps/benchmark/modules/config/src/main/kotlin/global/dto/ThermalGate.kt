package io.github.junekim0007.cryptobench.config.global.dto

// run.thermalGate: before each case process the host waits while the hottest named sensor is above baseline + margin or the status is above 0.
data class ThermalGate(
    val enabled: Boolean = true,
    val sensors: List<String> = emptyList(),
    val marginCelsius: Double = MARGIN_CELSIUS,
    val pollSeconds: Int = POLL_SECONDS,
    val timeoutSeconds: Int = TIMEOUT_SECONDS,
) {

    init {
        require(!enabled || sensors.isNotEmpty()) { "missing_field: run.thermalGate.sensors, the device's sensor names to gate on" }
        require(sensors.none { it.isBlank() }) { "invalid: run.thermalGate.sensors $sensors" }
        require(marginCelsius >= 0) { "negative: run.thermalGate.marginCelsius $marginCelsius" }
        require(pollSeconds >= 1) { "not_positive: run.thermalGate.pollSeconds $pollSeconds" }
        require(timeoutSeconds >= 0) { "negative: run.thermalGate.timeoutSeconds $timeoutSeconds" }
    }

    companion object {
        const val MARGIN_CELSIUS = 5.0
        const val POLL_SECONDS = 5
        const val TIMEOUT_SECONDS = 300
    }
}
