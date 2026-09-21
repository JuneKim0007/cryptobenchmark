package io.github.junekim0007.cryptobench.preparation.adapter

import io.github.junekim0007.cryptobench.preparation.port.Availability
import io.github.junekim0007.cryptobench.preparation.port.DeviceCapability
import io.github.junekim0007.cryptobench.discovery.contract.CapturedEnvironment
import io.github.junekim0007.cryptobench.discovery.contract.TrialOutcome
import io.github.junekim0007.cryptobench.discovery.contract.TrialReport
import io.github.junekim0007.cryptobench.discovery.query.CaptureQuery
import io.github.junekim0007.cryptobench.discovery.query.TrialQuery

class DiscoveryCapability(capture: CapturedEnvironment, trial: TrialReport) : DeviceCapability {

    init {
        require(capture.capturedAtMillis == trial.capturedAtMillis) {
            "mismatched_trial: capture ${capture.capturedAtMillis}, trial ${trial.capturedAtMillis}"
        }
    }

    private val captureQuery = CaptureQuery(capture)

    private val trialQuery = TrialQuery(trial)

    private val installed: List<String> = capture.providers.sortedBy { it.precedence }.map { it.name }

    override fun providers(): List<String> = installed

    override fun check(provider: String, type: String, algorithm: String): Availability {
        if (provider !in installed) {
            return Availability.Unavailable("provider_not_installed")
        }
        val registered = captureQuery.serviceOf(provider, type, algorithm)
        if (registered != null) {
            return availability(trialQuery.serviceTrial(provider, type, registered.algorithm)?.outcome, "instantiation_fails")
        }
        val base = algorithm.substringBefore('/', missingDelimiterValue = "")
        if (base.isEmpty()) {
            return Availability.Unavailable("not_registered")
        }
        val baseService = captureQuery.serviceOf(provider, type, base)
            ?: return Availability.Unavailable("not_registered")
        return availability(trialQuery.transformationTrial(provider, baseService.algorithm, algorithm)?.outcome, "transformation_fails")
    }

    private fun availability(outcome: TrialOutcome?, failure: String): Availability = when {
        outcome == null -> Availability.Unavailable("not_tried")
        outcome.instantiates -> Availability.Available
        else -> Availability.Unavailable(failure + ": " + outcome.error)
    }
}
