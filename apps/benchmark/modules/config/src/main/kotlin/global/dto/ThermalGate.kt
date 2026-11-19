package io.github.junekim0007.cryptobench.config.global.dto

import io.github.junekim0007.cryptobench.settings.Leaf
import io.github.junekim0007.cryptobench.settings.Nested
import io.github.junekim0007.cryptobench.settings.Section
import io.github.junekim0007.cryptobench.settings.Values

// run.thermalGate, absent is off: no run of a case may reach temperatureKeptCelsius on the phone's skin; a run must also start startMargin below it.
// Authored blocks hold only what they set; resolved() merges them over DEFAULTS key by key and checks the result.
data class ThermalGate(
    val temperatureKeptCelsius: Double? = null,
    val cooldownMinutes: Int? = null,
    val pollMinutes: Int? = null,
    val pollTerminateMinutes: Int? = null,
    val discardLimit: Int? = null,
    val onDiscardLimit: String? = null,
    val readRetries: Int? = null,
    val readRetrySeconds: Int? = null,
    val startMargin: StartMargin? = null,
) {

    /** This block over base key by key, then checked under path; without temperatureKeptCelsius it is refused. */
    fun resolved(base: ThermalGate, path: String): ThermalGate = GATE.merged(base, this).also { it.check(path) }

    private fun check(path: String) {
        val kept = temperatureKeptCelsius ?: throw IllegalArgumentException("missing_field: $path.temperatureKeptCelsius")
        require(kept > 0) { "not_positive: $path.temperatureKeptCelsius $kept" }
        require(cooldownMinutes!! >= 0) { "negative: $path.cooldownMinutes $cooldownMinutes" }
        require(pollMinutes!! >= 1) { "not_positive: $path.pollMinutes $pollMinutes" }
        require(pollTerminateMinutes!! >= pollMinutes) { "invalid: $path.pollTerminateMinutes $pollTerminateMinutes, below pollMinutes $pollMinutes" }
        require(discardLimit!! >= 1) { "not_positive: $path.discardLimit $discardLimit" }
        require(onDiscardLimit in ON_DISCARD_LIMIT) { "invalid: $path.onDiscardLimit $onDiscardLimit, expected one of $ON_DISCARD_LIMIT" }
        require(readRetries!! >= 0) { "negative: $path.readRetries $readRetries" }
        require(readRetrySeconds!! >= 0) { "negative: $path.readRetrySeconds $readRetrySeconds" }
        startMargin!!.check("$path.startMargin")
    }

    companion object {
        val ON_DISCARD_LIMIT = listOf("nextCase", "stop")

        val DEFAULTS = ThermalGate(null, 3, 1, 30, 5, ON_DISCARD_LIMIT.first(), 2, 1, StartMargin.DEFAULTS)

        val GATE: Section<ThermalGate> = Section(ThermalGate(), "") {
            listOf(
                Leaf("temperatureKeptCelsius", Values.decimal, { it.temperatureKeptCelsius }, { o, v -> o.copy(temperatureKeptCelsius = v) }),
                Leaf("cooldownMinutes", Values.whole, { it.cooldownMinutes }, { o, v -> o.copy(cooldownMinutes = v) }),
                Leaf("pollMinutes", Values.whole, { it.pollMinutes }, { o, v -> o.copy(pollMinutes = v) }),
                Leaf("pollTerminateMinutes", Values.whole, { it.pollTerminateMinutes }, { o, v -> o.copy(pollTerminateMinutes = v) }),
                Leaf("discardLimit", Values.whole, { it.discardLimit }, { o, v -> o.copy(discardLimit = v) }),
                Leaf("onDiscardLimit", Values.text(ON_DISCARD_LIMIT), { it.onDiscardLimit }, { o, v -> o.copy(onDiscardLimit = v) }),
                Leaf("readRetries", Values.whole, { it.readRetries }, { o, v -> o.copy(readRetries = v) }),
                Leaf("readRetrySeconds", Values.whole, { it.readRetrySeconds }, { o, v -> o.copy(readRetrySeconds = v) }),
                Nested("startMargin", StartMargin.MARGIN, { it.startMargin }, { o, v -> o.copy(startMargin = v) }),
            )
        }
    }
}

// Degrees Celsius below temperatureKeptCelsius that a run must start at; dynamic false keeps initialCelsius for the whole session.
data class StartMargin(
    val dynamic: Boolean? = null,
    val initialCelsius: Double? = null,
    val backoffFactor: Double? = null,
    val maximumCelsius: Double? = null,
    val cleanRunsToRecover: Int? = null,
    val recoveryCelsius: Double? = null,
) {

    internal fun check(path: String) {
        require(initialCelsius!! >= 0) { "negative: $path.initialCelsius $initialCelsius" }
        require(backoffFactor!! >= 1) { "invalid: $path.backoffFactor $backoffFactor, at least 1" }
        require(maximumCelsius!! >= initialCelsius) { "invalid: $path.maximumCelsius $maximumCelsius, below initialCelsius $initialCelsius" }
        require(cleanRunsToRecover!! >= 1) { "not_positive: $path.cleanRunsToRecover $cleanRunsToRecover" }
        require(recoveryCelsius!! >= 0) { "negative: $path.recoveryCelsius $recoveryCelsius" }
    }

    companion object {
        val DEFAULTS = StartMargin(true, 0.25, 2.0, 3.0, 10, 0.05)

        val MARGIN: Section<StartMargin> = Section(StartMargin(), "startMargin.") {
            listOf(
                Leaf("dynamic", Values.boolean, { it.dynamic }, { o, v -> o.copy(dynamic = v) }),
                Leaf("initialCelsius", Values.decimal, { it.initialCelsius }, { o, v -> o.copy(initialCelsius = v) }),
                Leaf("backoffFactor", Values.decimal, { it.backoffFactor }, { o, v -> o.copy(backoffFactor = v) }),
                Leaf("maximumCelsius", Values.decimal, { it.maximumCelsius }, { o, v -> o.copy(maximumCelsius = v) }),
                Leaf("cleanRunsToRecover", Values.whole, { it.cleanRunsToRecover }, { o, v -> o.copy(cleanRunsToRecover = v) }),
                Leaf("recoveryCelsius", Values.decimal, { it.recoveryCelsius }, { o, v -> o.copy(recoveryCelsius = v) }),
            )
        }
    }
}
