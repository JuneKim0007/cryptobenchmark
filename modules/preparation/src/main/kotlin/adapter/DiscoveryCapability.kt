package io.github.junekim0007.cryptobench.preparation.adapter

import io.github.junekim0007.cryptobench.preparation.device.CaptureFile
import io.github.junekim0007.cryptobench.preparation.device.ServiceName
import io.github.junekim0007.cryptobench.preparation.device.TrialFile
import io.github.junekim0007.cryptobench.preparation.device.dto.CapturedDevice
import io.github.junekim0007.cryptobench.preparation.device.dto.CapturedService
import io.github.junekim0007.cryptobench.preparation.device.dto.TrialledDevice
import io.github.junekim0007.cryptobench.preparation.device.dto.TrialledService
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
        val registered = serviceOf(provider, type, algorithm)
        if (registered != null) {
            val trialled = trialsByProvider[provider]?.get(ServiceName.of(type, registered.algorithm))
            return availability(trialled?.instantiates, trialled?.error, "instantiation_fails")
        }
        val base = algorithm.substringBefore('/', missingDelimiterValue = "")
        if (base.isEmpty()) {
            return Availability.Unavailable("not_registered")
        }
        val baseService = serviceOf(provider, type, base) ?: return Availability.Unavailable("not_registered")
        val transformation = trialsByProvider[provider]
            ?.get(ServiceName.of(CIPHER, baseService.algorithm))
            ?.transformations
            ?.firstOrNull { it.name.equals(algorithm, ignoreCase = true) }
        return availability(transformation?.instantiates, transformation?.error, "transformation_fails")
    }

    private fun serviceOf(provider: String, type: String, algorithmOrAlias: String): CapturedService? =
        servicesByProvider[provider]?.get(ServiceName.of(type, algorithmOrAlias))

    private fun availability(instantiates: Boolean?, error: String?, failure: String): Availability = when {
        instantiates == null -> Availability.Unavailable("not_tried")
        instantiates -> Availability.Available
        else -> Availability.Unavailable(failure + ": " + error.orEmpty())
    }

    private companion object {
        const val CIPHER = "Cipher"
    }
}
