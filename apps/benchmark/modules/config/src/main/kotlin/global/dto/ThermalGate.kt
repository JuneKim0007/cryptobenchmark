package io.github.junekim0007.cryptobench.config.global.dto

// run.thermalGate, absent is off: no run of a case may reach temperatureKeptCelsius on the phone's skin; a run must also start startMargin below it.
data class ThermalGate(
    val temperatureKeptCelsius: Double,
    val cooldownMinutes: Int = COOLDOWN_MINUTES,
    val pollMinutes: Int = POLL_MINUTES,
    val pollTerminateMinutes: Int = POLL_TERMINATE_MINUTES,
    val discardLimit: Int = DISCARD_LIMIT,
    val onDiscardLimit: String = NEXT_CASE,
    val readRetries: Int = READ_RETRIES,
    val readRetrySeconds: Int = READ_RETRY_SECONDS,
    val startMargin: StartMargin = StartMargin(),
) {

    init {
        require(temperatureKeptCelsius > 0) { "not_positive: run.thermalGate.temperatureKeptCelsius $temperatureKeptCelsius" }
        require(cooldownMinutes >= 0) { "negative: run.thermalGate.cooldownMinutes $cooldownMinutes" }
        require(pollMinutes >= 1) { "not_positive: run.thermalGate.pollMinutes $pollMinutes" }
        require(pollTerminateMinutes >= pollMinutes) { "invalid: run.thermalGate.pollTerminateMinutes $pollTerminateMinutes, below pollMinutes $pollMinutes" }
        require(discardLimit >= 1) { "not_positive: run.thermalGate.discardLimit $discardLimit" }
        require(onDiscardLimit in ON_DISCARD_LIMIT) { "invalid: run.thermalGate.onDiscardLimit $onDiscardLimit, expected one of $ON_DISCARD_LIMIT" }
        require(readRetries >= 0) { "negative: run.thermalGate.readRetries $readRetries" }
        require(readRetrySeconds >= 0) { "negative: run.thermalGate.readRetrySeconds $readRetrySeconds" }
    }

    companion object {
        const val COOLDOWN_MINUTES = 3
        const val POLL_MINUTES = 1
        const val POLL_TERMINATE_MINUTES = 30
        const val DISCARD_LIMIT = 5
        const val NEXT_CASE = "nextCase"
        const val READ_RETRIES = 2
        const val READ_RETRY_SECONDS = 1
        val ON_DISCARD_LIMIT = listOf(NEXT_CASE, "stop")
    }
}

// Degrees Celsius below temperatureKeptCelsius that a run must start at; dynamic false keeps initialCelsius for the whole session.
data class StartMargin(
    val dynamic: Boolean = true,
    val initialCelsius: Double = 0.25,
    val backoffFactor: Double = 2.0,
    val maximumCelsius: Double = 3.0,
    val cleanRunsToRecover: Int = 10,
    val recoveryCelsius: Double = 0.05,
) {

    init {
        require(initialCelsius >= 0) { "negative: run.thermalGate.startMargin.initialCelsius $initialCelsius" }
        require(backoffFactor >= 1) { "invalid: run.thermalGate.startMargin.backoffFactor $backoffFactor, at least 1" }
        require(maximumCelsius >= initialCelsius) { "invalid: run.thermalGate.startMargin.maximumCelsius $maximumCelsius, below initialCelsius $initialCelsius" }
        require(cleanRunsToRecover >= 1) { "not_positive: run.thermalGate.startMargin.cleanRunsToRecover $cleanRunsToRecover" }
        require(recoveryCelsius >= 0) { "negative: run.thermalGate.startMargin.recoveryCelsius $recoveryCelsius" }
    }
}
