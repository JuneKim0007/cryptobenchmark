package io.github.junekim0007.cryptobench.preparation.adapter

import io.github.junekim0007.cryptobench.preparation.device.CaptureFile
import io.github.junekim0007.cryptobench.preparation.device.ServiceName
import io.github.junekim0007.cryptobench.preparation.device.TrialFile
import io.github.junekim0007.cryptobench.preparation.device.dto.CapturedDevice
import io.github.junekim0007.cryptobench.preparation.device.dto.CapturedService
import io.github.junekim0007.cryptobench.preparation.device.dto.TrialledDevice
import io.github.junekim0007.cryptobench.preparation.device.dto.TrialledService
import io.github.junekim0007.cryptobench.preparation.key.plan.KeyCandidate
import io.github.junekim0007.cryptobench.preparation.port.Availability
import io.github.junekim0007.cryptobench.preparation.port.DeviceCapability
import java.io.File

class DiscoveryCapability(capture: CapturedDevice, trial: TrialledDevice) : DeviceCapability {

    constructor(captureFile: File, trialFile: File) : this(CaptureFile.read(captureFile), TrialFile.read(trialFile))

    init {
        require(capture.capturedAtMillis == trial.capturedAtMillis) {
            "mismatched_trial: capture ${capture.capturedAtMillis}, trial ${trial.capturedAtMillis}"
        }
    }

    private val installed: List<String> = capture.providers.sortedBy { it.precedence }.map { it.name }

    private val servicesByProvider: Map<String, Map<ServiceName, CapturedService>> =
        capture.providers.associate { provider ->
            provider.name to HashMap<ServiceName, CapturedService>().apply {
                for (service in provider.services) {
                    put(ServiceName.of(service.type, service.algorithm), service)
                    for (alias in service.aliases) {
                        put(ServiceName.of(service.type, alias), service)
                    }
                }
            }
        }

    private val trialsByProvider: Map<String, Map<ServiceName, TrialledService>> =
        trial.services.groupBy { it.provider }.mapValues { (_, services) ->
            services.associateBy { ServiceName.of(it.type, it.algorithm) }
        }

    override fun providers(): List<String> = installed

    override fun check(provider: String, type: String, algorithm: String): Availability {
        if (provider !in installed) {
            return Availability.Unavailable("provider_not_installed")
        }
        val found = trialled(provider, type, algorithm) ?: return Availability.Unavailable("not_registered")
        return when (found.instantiates) {
            null -> Availability.Unavailable("not_tried")
            true -> Availability.Available
            false -> Availability.Unavailable(found.failure + ": " + found.error)
        }
    }

    override fun measuredKey(provider: String, type: String, algorithm: String): KeyCandidate? =
        trialled(provider, type, algorithm)?.takeIf { it.keyAlgorithm.isNotBlank() }?.let { KeyCandidate(it.keyAlgorithm, it.fixedKeySize) }

    // The trial of a registered name or alias, else of a transformation on its base service; null when neither is registered.
    private fun trialled(provider: String, type: String, algorithm: String): Trialled? {
        val trials = trialsByProvider[provider]
        serviceOf(provider, type, algorithm)?.let { registered ->
            val service = trials?.get(ServiceName.of(type, registered.algorithm))
            return Trialled(service?.instantiates, service?.error.orEmpty(), service?.keyAlgorithm.orEmpty(), service?.fixedKeySize, "instantiation_fails")
        }
        val base = algorithm.substringBefore('/', missingDelimiterValue = "").ifEmpty { return null }
        val baseService = serviceOf(provider, type, base) ?: return null
        val transformation = trials?.get(ServiceName.of(type, baseService.algorithm))?.transformations?.firstOrNull { it.name.equals(algorithm, ignoreCase = true) }
        return Trialled(transformation?.instantiates, transformation?.error.orEmpty(), transformation?.keyAlgorithm.orEmpty(), transformation?.fixedKeySize, "transformation_fails")
    }

    private fun serviceOf(provider: String, type: String, algorithmOrAlias: String): CapturedService? =
        servicesByProvider[provider]?.get(ServiceName.of(type, algorithmOrAlias))

    private class Trialled(val instantiates: Boolean?, val error: String, val keyAlgorithm: String, val fixedKeySize: Int?, val failure: String)
}
